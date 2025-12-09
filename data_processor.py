import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict

class InventoryAnalyzer:
    def __init__(self, excel_file):
        """Initialize analyzer with Excel file path"""
        self.df = pd.read_excel(excel_file)
        # Ensure key columns are strings for consistent matching
        for col in ['Material', 'Plant', 'Storage Location']:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str)
        self.process_data()
    
    def process_data(self):
        """Process raw data to calculate current inventory levels"""
        # Convert dates
        self.df['Document Date'] = pd.to_datetime(self.df['Document Date'], errors='coerce')
        self.df['Posting Date'] = pd.to_datetime(self.df['Posting Date'], errors='coerce')
        
        # Calculate current inventory per site (Plant), storage location, and material
        # We need to track Quantity and Value
        inventory = defaultdict(lambda: {
            'qty': 0.0, 
            'value': 0.0, 
            'last_active': pd.Timestamp.min
        })
        
        for _, row in self.df.iterrows():
            site = str(row['Plant']) if pd.notna(row['Plant']) else 'Unknown'
            storage_loc = str(row['Storage Location']) if pd.notna(row['Storage Location']) else 'N/A'
            material = str(row['Material'])
            material_desc = str(row['Material Description'])
            
            quantity = float(row['Quantity']) if pd.notna(row['Quantity']) else 0
            value = float(row['Amt.in Loc.Cur.']) if pd.notna(row['Amt.in Loc.Cur.']) else 0
            posting_date = row['Posting Date']
            
            key = (site, storage_loc, material, material_desc)
            
            inventory[key]['qty'] += quantity
            inventory[key]['value'] += value
            if pd.notna(posting_date) and posting_date > inventory[key]['last_active']:
                inventory[key]['last_active'] = posting_date
        
        # Convert to DataFrame
        inventory_list = []
        for (site, storage_loc, material, material_desc), data in inventory.items():
            inventory_list.append({
                'Site': site,
                'Storage Location': storage_loc,
                'Material': material,
                'Material Description': material_desc,
                'Current Quantity': data['qty'],
                'Total Value': data['value'],
                'Last Active': data['last_active'].strftime('%Y-%m-%d') if data['last_active'] != pd.Timestamp.min else 'N/A',
                'Unit': self._get_unit(material)
            })
        
        self.inventory_df = pd.DataFrame(inventory_list)
        
        # Calculate statistics
        self._calculate_statistics()
    
    def _get_unit(self, material):
        """Get unit for a material from original data"""
        material_rows = self.df[self.df['Material'] == material]
        if len(material_rows) > 0:
            unit = material_rows.iloc[0]['Unit of Entry']
            return str(unit) if pd.notna(unit) else 'EA'
        return 'EA'
    
    def _calculate_statistics(self):
        """Calculate statistics for threshold determination"""
        if len(self.inventory_df) == 0:
            self.median_qty = 0
            self.mean_qty = 0
            self.std_qty = 0
            return
        
        quantities = self.inventory_df['Current Quantity'].abs()
        self.median_qty = quantities.median()
        self.mean_qty = quantities.mean()
        self.std_qty = quantities.std()
    
    def get_site_summary(self):
        """Get summary statistics per site"""
        summary = self.inventory_df.groupby('Site').agg({
            'Current Quantity': 'sum',
            'Total Value': 'sum',
            'Material': 'nunique'
        }).round(2)
        
        summary.columns = ['Total Quantity', 'Total Value', 'Unique Materials']
        return summary.reset_index().to_dict('records')
    
    def get_shortage_items(self, threshold_percentile=None):
        """Identify items that are short (low inventory)"""
        # If threshold is None, return all negative items
        if threshold_percentile is None:
            shortages = self.inventory_df[
                self.inventory_df['Current Quantity'] < 0
            ].copy()
        else:
            threshold = self.inventory_df['Current Quantity'].quantile(threshold_percentile / 100)
            shortages = self.inventory_df[
                (self.inventory_df['Current Quantity'] < threshold) & 
                (self.inventory_df['Current Quantity'] < 0)
            ].copy()
        
        shortages = shortages.sort_values('Current Quantity')
        
        # Binning for levels
        if len(shortages) > 0:
            shortages['Shortage Level'] = pd.cut(
                shortages['Current Quantity'],
                bins=[-np.inf, -self.mean_qty, -self.median_qty, 0],
                labels=['Critical', 'High', 'Moderate']
            )
            # Handle NaN levels (if binning fails or values are outside)
            shortages['Shortage Level'] = shortages['Shortage Level'].fillna('High')
        else:
             shortages['Shortage Level'] = []

        return shortages.to_dict('records')
    
    def get_critical_items(self, threshold_multiplier=2):
        """Identify critical items (very low or negative inventory)"""
        critical_threshold = -abs(self.mean_qty) * threshold_multiplier
        
        critical = self.inventory_df[
            self.inventory_df['Current Quantity'] <= critical_threshold
        ].copy()
        
        critical = critical.sort_values('Current Quantity')
        return critical.to_dict('records')
    
    def get_abundant_items(self, threshold_percentile=90):
        """Identify items that are abundant (high inventory)"""
        threshold = self.inventory_df['Current Quantity'].quantile(threshold_percentile / 100)
        
        abundant = self.inventory_df[
            self.inventory_df['Current Quantity'] > threshold
        ].copy()
        
        if len(abundant) == 0:
            return []
        
        abundant = abundant.sort_values('Current Quantity', ascending=False)
        
        # Create bins dynamically to avoid errors
        max_qty = abundant['Current Quantity'].max()
        bin1 = threshold
        bin2 = max(bin1, self.median_qty * 2) if self.median_qty > 0 else bin1 * 2
        bin3 = max(bin2, self.mean_qty * 3) if self.mean_qty > 0 else bin2 * 2
        
        # Ensure bins are in ascending order
        bins = sorted([bin1, bin2, bin3, max_qty + 1])
        bins = [b for b in bins if b > threshold] + [np.inf]
        bins = [threshold] + bins
        
        if len(bins) < 3:
            # Fallback: simple categorization
            abundant['Abundance Level'] = abundant['Current Quantity'].apply(
                lambda x: 'Very High' if x > self.mean_qty * 3 else ('High' if x > self.median_qty * 2 else 'Moderate')
            )
        else:
            try:
                abundant['Abundance Level'] = pd.cut(
                    abundant['Current Quantity'],
                    bins=bins[:4] if len(bins) >= 4 else bins,
                    labels=['Moderate', 'High', 'Very High'][:len(bins)-1],
                    include_lowest=True
                )
            except:
                # Fallback if cut still fails
                abundant['Abundance Level'] = abundant['Current Quantity'].apply(
                    lambda x: 'Very High' if x > self.mean_qty * 3 else ('High' if x > self.median_qty * 2 else 'Moderate')
                )
        
        return abundant.to_dict('records')
    
    def get_shipping_recommendations(self):
        """Recommend items that should be shipped between sites"""
        recommendations = []
        
        # Group by material to find imbalances
        material_sites = defaultdict(list)
        for _, row in self.inventory_df.iterrows():
            material_sites[row['Material']].append({
                'Site': row['Site'],
                'Quantity': row['Current Quantity'],
                'Material Description': row['Material Description']
            })
        
        # Find materials with both surplus and shortage
        for material, sites_data in material_sites.items():
            if len(sites_data) < 2:
                continue
            
            # Find sites with surplus and shortage
            surplus_sites = [s for s in sites_data if s['Quantity'] > self.median_qty]
            shortage_sites = [s for s in sites_data if s['Quantity'] < 0]
            
            if surplus_sites and shortage_sites:
                for surplus in surplus_sites:
                    for shortage in shortage_sites:
                        transfer_qty = min(
                            abs(surplus['Quantity'] - self.median_qty),
                            abs(shortage['Quantity'])
                        )
                        
                        if transfer_qty > 0:
                            recommendations.append({
                                'Material': material,
                                'Material Description': surplus['Material Description'],
                                'From Site': surplus['Site'],
                                'To Site': shortage['Site'],
                                'Recommended Quantity': round(transfer_qty, 2),
                                'Priority': 'High' if shortage['Quantity'] < -self.mean_qty else 'Medium'
                            })
        
        return sorted(recommendations, key=lambda x: (x['Priority'] == 'High', -x['Recommended Quantity']), reverse=True)
    
    def get_material_analysis(self, material=None):
        """Get detailed analysis for a specific material across all sites"""
        if material:
            return self.inventory_df[
                self.inventory_df['Material'] == material
            ].to_dict('records')
        return self.inventory_df.to_dict('records')

    def get_material_details(self, material):
        """Get granular details including Storage Location for a material"""
        # Filter original DF
        material_df = self.df[self.df['Material'] == str(material)].copy()
        
        # 1. Breakdown by Storage Location
        storage_loc_stats = material_df.groupby(['Plant', 'Storage Location']).agg({
            'Quantity': 'sum',
            'Amt.in Loc.Cur.': 'sum'
        }).reset_index()
        
        storage_loc_stats.columns = ['Site', 'Storage Location', 'Quantity', 'Value']
        
        # 2. Recent Transactions
        recent_tx = material_df.sort_values('Posting Date', ascending=False).head(10)
        transactions = []
        for _, row in recent_tx.iterrows():
            transactions.append({
                'Date': row['Posting Date'].strftime('%Y-%m-%d') if pd.notna(row['Posting Date']) else 'N/A',
                'Type': row['Movement Type'],
                'Qty': row['Quantity'],
                'Site': row['Plant'],
                'Storage': row['Storage Location'],
                'Text': str(row['Text']) if pd.notna(row['Text']) else ''
            })
            
        return {
            'locations': storage_loc_stats.to_dict('records'),
            'transactions': transactions
        }

    def get_site_inventory(self, site=None):
        """Get inventory for a specific site or all sites"""
        if site:
            return self.inventory_df[
                self.inventory_df['Site'] == site
            ].to_dict('records')
        return self.inventory_df.to_dict('records')
    
    def get_bottleneck_analysis(self):
        """Identify bottlenecks - sites/storage locations with most critical issues"""
        bottlenecks = []
        
        # 1. Site-level bottlenecks (shortages by site)
        site_shortages = self.inventory_df[self.inventory_df['Current Quantity'] < 0].groupby('Site').agg({
            'Current Quantity': ['sum', 'count'],
            'Total Value': 'sum'
        }).reset_index()
        site_shortages.columns = ['Site', 'Total Shortage Qty', 'Item Count', 'Total Value Impact']
        site_shortages = site_shortages.sort_values('Total Value Impact')
        site_shortages['Bottleneck Type'] = 'Site'
        site_shortages['Priority'] = site_shortages['Total Value Impact'].apply(
            lambda x: 'Critical' if abs(x) > abs(self.inventory_df['Total Value'].sum() * 0.1) else 'High'
        )
        
        # 2. Storage Location bottlenecks
        loc_shortages = self.inventory_df[self.inventory_df['Current Quantity'] < 0].groupby(['Site', 'Storage Location']).agg({
            'Current Quantity': ['sum', 'count'],
            'Total Value': 'sum'
        }).reset_index()
        loc_shortages.columns = ['Site', 'Storage Location', 'Total Shortage Qty', 'Item Count', 'Total Value Impact']
        loc_shortages = loc_shortages.sort_values('Total Value Impact')
        loc_shortages['Bottleneck Type'] = 'Storage Location'
        loc_shortages['Priority'] = loc_shortages['Total Value Impact'].apply(
            lambda x: 'Critical' if abs(x) > abs(self.inventory_df['Total Value'].sum() * 0.05) else 'High'
        )
        
        # 3. Material bottlenecks (highest value impact shortages)
        material_shortages = self.inventory_df[self.inventory_df['Current Quantity'] < 0].groupby('Material').agg({
            'Current Quantity': 'sum',
            'Total Value': 'sum',
            'Material Description': 'first',
            'Site': lambda x: ', '.join(x.unique())
        }).reset_index()
        material_shortages.columns = ['Material', 'Total Shortage Qty', 'Total Value Impact', 'Material Description', 'Affected Sites']
        material_shortages = material_shortages.sort_values('Total Value Impact')
        material_shortages['Bottleneck Type'] = 'Material'
        material_shortages['Priority'] = material_shortages['Total Value Impact'].apply(
            lambda x: 'Critical' if abs(x) > abs(self.inventory_df['Total Value'].sum() * 0.05) else 'High'
        )
        
        return {
            'sites': site_shortages.to_dict('records'),
            'locations': loc_shortages.to_dict('records'),
            'materials': material_shortages.to_dict('records')
        }
    
    def get_focus_areas(self):
        """Identify focus areas - where to prioritize attention"""
        focus_areas = []
        
        # 1. High-value shortages (biggest financial impact)
        high_value_shortages = self.inventory_df[
            (self.inventory_df['Current Quantity'] < 0) & 
            (self.inventory_df['Total Value'] < 0)
        ].copy()
        high_value_shortages = high_value_shortages.sort_values('Total Value')
        high_value_shortages['Focus Reason'] = 'High Value Impact'
        high_value_shortages['Action'] = 'Urgent Replenishment Required'
        
        # 2. Critical quantity shortages (largest quantity gaps)
        critical_qty = self.inventory_df[
            self.inventory_df['Current Quantity'] < -abs(self.mean_qty)
        ].copy()
        critical_qty = critical_qty.sort_values('Current Quantity')
        critical_qty['Focus Reason'] = 'Critical Quantity Gap'
        critical_qty['Action'] = 'Immediate Stock Transfer'
        
        # 3. Sites with multiple shortages
        site_issues = self.inventory_df[self.inventory_df['Current Quantity'] < 0].groupby('Site').agg({
            'Material': 'count',
            'Current Quantity': 'sum',
            'Total Value': 'sum'
        }).reset_index()
        site_issues.columns = ['Site', 'Shortage Count', 'Total Shortage Qty', 'Total Value Impact']
        site_issues = site_issues.sort_values('Shortage Count', ascending=False)
        site_issues['Focus Reason'] = 'Multiple Shortages'
        site_issues['Action'] = 'Site-Level Review Required'
        
        # 4. Storage locations with critical issues
        loc_issues = self.inventory_df[self.inventory_df['Current Quantity'] < 0].groupby(['Site', 'Storage Location']).agg({
            'Material': 'count',
            'Current Quantity': 'sum',
            'Total Value': 'sum'
        }).reset_index()
        loc_issues.columns = ['Site', 'Storage Location', 'Shortage Count', 'Total Shortage Qty', 'Total Value Impact']
        loc_issues = loc_issues.sort_values('Shortage Count', ascending=False)
        loc_issues['Focus Reason'] = 'Location Issues'
        loc_issues['Action'] = 'Storage Location Audit'
        
        return {
            'high_value': high_value_shortages.head(20).to_dict('records'),
            'critical_quantity': critical_qty.head(20).to_dict('records'),
            'site_issues': site_issues.to_dict('records'),
            'location_issues': loc_issues.head(20).to_dict('records')
        }
    
    def get_movement_recommendations(self):
        """Enhanced movement recommendations with detailed analysis"""
        recommendations = []
        
        # Group by material to find imbalances
        material_sites = defaultdict(list)
        for _, row in self.inventory_df.iterrows():
            material_sites[row['Material']].append({
                'Site': row['Site'],
                'Storage Location': row['Storage Location'],
                'Quantity': row['Current Quantity'],
                'Value': row['Total Value'],
                'Material Description': row['Material Description']
            })
        
        # Find materials with both surplus and shortage
        for material, sites_data in material_sites.items():
            if len(sites_data) < 2:
                continue
            
            # Find sites with surplus and shortage
            surplus_sites = [s for s in sites_data if s['Quantity'] > self.median_qty]
            shortage_sites = [s for s in sites_data if s['Quantity'] < 0]
            
            if surplus_sites and shortage_sites:
                for surplus in surplus_sites:
                    for shortage in shortage_sites:
                        transfer_qty = min(
                            abs(surplus['Quantity'] - self.median_qty),
                            abs(shortage['Quantity'])
                        )
                        
                        if transfer_qty > 0:
                            # Calculate value impact
                            unit_value = abs(surplus['Value']) / abs(surplus['Quantity']) if surplus['Quantity'] != 0 else 0
                            transfer_value = transfer_qty * unit_value
                            
                            # Determine urgency
                            urgency_score = abs(shortage['Quantity']) / abs(self.mean_qty) if self.mean_qty != 0 else 0
                            urgency = 'Critical' if urgency_score > 2 else ('High' if urgency_score > 1 else 'Medium')
                            
                            recommendations.append({
                                'Material': material,
                                'Material Description': surplus['Material Description'],
                                'From Site': surplus['Site'],
                                'From Storage Location': surplus['Storage Location'],
                                'To Site': shortage['Site'],
                                'To Storage Location': shortage['Storage Location'],
                                'Available Qty': round(surplus['Quantity'], 2),
                                'Required Qty': round(abs(shortage['Quantity']), 2),
                                'Recommended Quantity': round(transfer_qty, 2),
                                'Estimated Value': round(transfer_value, 2),
                                'Priority': urgency,
                                'Impact': 'High' if transfer_value > abs(self.mean_qty * unit_value) else 'Medium'
                            })
        
        return sorted(recommendations, key=lambda x: (
            x['Priority'] == 'Critical',
            x['Priority'] == 'High',
            -x['Estimated Value']
        ), reverse=True)

    def get_top_shortages_by_value(self, limit=10):
        """Top shortages ranked by absolute value impact"""
        shortages = self.inventory_df[self.inventory_df['Current Quantity'] < 0].copy()
        if shortages.empty:
            return []
        shortages['Value Impact'] = shortages['Total Value']
        shortages = shortages.sort_values('Value Impact')
        return shortages.head(limit).to_dict('records')

    def get_inactive_stock(self, days=90, limit=20):
        """Stock that has not moved for given days"""
        if 'Last Active' not in self.inventory_df.columns:
            return []
        inactive = self.inventory_df.copy()
        inactive['Last Active Date'] = pd.to_datetime(inactive['Last Active'], errors='coerce')
        cutoff = pd.Timestamp.today() - pd.Timedelta(days=days)
        inactive = inactive[(inactive['Last Active Date'].isna()) | (inactive['Last Active Date'] < cutoff)]
        inactive = inactive.sort_values('Last Active Date', ascending=True)
        return inactive.head(limit).to_dict('records')
    
    def get_dashboard_stats(self):
        """Get overall dashboard statistics"""
        total_items = len(self.inventory_df)
        total_sites = self.inventory_df['Site'].nunique()
        total_materials = self.inventory_df['Material'].nunique()
        
        negative_items = len(self.inventory_df[self.inventory_df['Current Quantity'] < 0])
        positive_items = len(self.inventory_df[self.inventory_df['Current Quantity'] > 0])
        
        total_quantity = self.inventory_df['Current Quantity'].sum()
        total_value = self.inventory_df['Total Value'].sum()
        
        return {
            'total_items': total_items,
            'total_sites': total_sites,
            'total_materials': total_materials,
            'negative_items': negative_items,
            'positive_items': positive_items,
            'total_quantity': round(total_quantity, 2),
            'total_value': round(total_value, 2),
            'avg_quantity': round(self.mean_qty, 2),
            'median_quantity': round(self.median_qty, 2)
        }
