import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def generate_chart_from_json(json_file_path, di_set_id, output_dir="charts"):
    """
    Finds a specific DI set in a JSON file, generates a chart, 
    and saves it as a PNG image.
    
    Args:
        json_file_path (str): The path to the main JSON file containing DI sets.
        di_set_id (str): The specific ID of the DI set to generate a chart for.
        output_dir (str): The directory where the chart image will be saved.
        
    Returns:
        str: The file path of the generated chart image, or None if failed.
    """
    
    # Create the output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            all_data = json.load(f)

        # Find the specific DI set by its ID
        target_set = None
        # Assuming the JSON contains a list of DI sets
        for di_set in all_data:
            if di_set.get('di_set_id') == di_set_id:
                target_set = di_set
                break
        
        if not target_set:
            print(f"❌ Error: DI Set ID '{di_set_id}' not found in {json_file_path}")
            return None

        data_source = target_set['data_source']
        chart_type = data_source['type']
        title = data_source['title']
        
        # Handle both nested and flat data structures
        if 'data' in data_source:
            data = data_source['data']
        else:
            data = data_source
        
        # --- Plotting Logic ---
        # Try different seaborn styles, fallback to default if not available
        try:
            plt.style.use('seaborn-v0_8-whitegrid')
        except OSError:
            try:
                plt.style.use('seaborn-whitegrid')
            except OSError:
                plt.style.use('default')
                print("⚠️ Using default matplotlib style")
        
        fig, ax = plt.subplots(figsize=(10, 6)) # Create a figure and axes

        # --- Bar or Line Chart Logic ---
        if chart_type in ['bar_chart', 'line_chart']:
            # Convert data to a pandas DataFrame for easy plotting
            df_data = []
            categories = data.get('categories', [])
            series_data = data.get('series', [])
            
            if not categories or not series_data:
                print(f"❌ Error: Missing categories or series data in {di_set_id}")
                return None
            
            for series in series_data:
                series_name = series.get('name', 'Unknown')
                values = series.get('values', [])
                for i, value in enumerate(values):
                    if i < len(categories):  # Ensure we don't go out of bounds
                        df_data.append([categories[i], series_name, value])
            
            if not df_data:
                print(f"❌ Error: No data to plot for {di_set_id}")
                return None
            
            df = pd.DataFrame(df_data, columns=['Category', 'Series', 'Value'])

            if chart_type == 'bar_chart':
                sns.barplot(data=df, x='Category', y='Value', hue='Series', ax=ax)
            elif chart_type == 'line_chart':
                sns.lineplot(data=df, x='Category', y='Value', hue='Series', marker='o', ax=ax)

            ax.set_xlabel("Category")
            ax.set_ylabel("Value")

        # --- Pie Chart Logic ---
        elif chart_type == 'pie_chart':
            labels = data.get('labels', [])
            values = data.get('values', [])
            
            if not labels or not values:
                print(f"❌ Error: Missing labels or values data for pie chart in {di_set_id}")
                return None
                
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.axis('equal') # Equal aspect ratio ensures that pie is drawn as a circle.

        else:
            print(f"⚠️ Warning: Chart type '{chart_type}' not supported yet.")
            return None
        
        ax.set_title(title, fontsize=16, weight='bold')
        plt.tight_layout() # Adjust layout to prevent labels overlapping

        # --- Save the File ---
        output_filename = f"{di_set_id}.png"
        output_path = Path(output_dir) / output_filename
        plt.savefig(output_path)
        plt.close(fig) # Close the figure to free up memory

        print(f"✅ Chart generated successfully: {output_path}")
        return str(output_path)

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return None


def generate_all_charts(json_file_path, output_dir="charts"):
    """Generate charts for all DI sets in the JSON file"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
        
        print(f"📊 Generating charts for {len(all_data)} DI sets...")
        successful = 0
        failed = 0
        
        for i, di_set in enumerate(all_data):
            di_set_id = di_set.get('di_set_id', f'UNKNOWN_{i}')
            print(f"🔄 Processing {i+1}/{len(all_data)}: {di_set_id}")
            
            result = generate_chart_from_json(json_file_path, di_set_id, output_dir)
            if result:
                successful += 1
            else:
                failed += 1
        
        print(f"\n🎉 Chart generation complete!")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📁 Charts saved in: {output_dir}/")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")

# --- EXAMPLE USAGE ---
if __name__ == "__main__":
    # Generate chart for a specific DI set
    json_path = "data/generated/quant_questions/di_bar_questions.json"
    set_id_to_generate = "DI_BAR_CHART_001"
    
    print("🎯 Generating single chart...")
    generate_chart_from_json(json_file_path=json_path, di_set_id=set_id_to_generate)
    
    print("\n" + "="*50)
    print("🎯 Generating all charts...")
    generate_all_charts(json_path, "charts")