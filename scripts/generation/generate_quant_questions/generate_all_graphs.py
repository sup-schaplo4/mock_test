import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import textwrap

def generate_charts_from_master_file(json_file_path, output_dir="output_charts"):
    """
    Reads the DI master question bank, iterates through every DI set,
    and generates a high-resolution PNG image for each chart or table.
    """
    print("🚀 Starting chart generation process...")
    
    # Create the output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract DI sets from the questions array
        all_di_sets = data.get('questions', [])
        total_sets = len(all_di_sets)
        print(f"Found {total_sets} DI sets to process.")

        for i, di_set in enumerate(all_di_sets):
            di_set_id = di_set.get('di_set_id', f'unknown_set_{i+1}')
            data_source = di_set.get('data_source', {})
            chart_type = data_source.get('type')
            
            print(f"Processing set {i+1}/{total_sets}: {di_set_id} ({chart_type})...")

            if not chart_type or chart_type == 'caselet':
                print(f"  -> Skipping '{di_set_id}' (Caselet or no chart type).")
                continue

            # --- PLOTTING LOGIC ---
            # Set high resolution by using dpi=300. This is the key to fixing blurry images.
            fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
            
            # Get data - check both direct data and nested data structure
            data = data_source.get('data', {})
            if not data:
                data = data_source

            if chart_type == 'table':
                headers = data.get('headers', [])
                rows = data.get('rows', [])
                if not headers or not rows:
                    print(f"  -> Skipping '{di_set_id}' (Table data is empty).")
                    plt.close(fig)
                    continue

                ax.axis('off') # Hide the chart axes for a clean table image
                table = ax.table(cellText=rows, colLabels=headers, loc='center', cellLoc='center')
                table.auto_set_font_size(False)
                table.set_fontsize(10)
                table.scale(1.2, 1.2) # Adjust table scale if needed

            elif chart_type in ['bar_chart', 'line_chart']:
                # Handle both 'categories' and 'x_axis' for different chart types
                categories = data.get('categories', [])
                if not categories:
                    categories = data.get('x_axis', [])
                
                series_list = data.get('series', [])
                if not categories or not series_list:
                    print(f"  -> Skipping '{di_set_id}' (Chart data is empty).")
                    plt.close(fig)
                    continue

                # Convert data to a pandas DataFrame for easy plotting
                df_data = []
                for series in series_list:
                    series_name = series.get('name')
                    for j, value in enumerate(series.get('values', [])):
                        df_data.append([categories[j], series_name, value])
                
                df = pd.DataFrame(df_data, columns=['Category', 'Series', 'Value'])

                if chart_type == 'bar_chart':
                    sns.barplot(data=df, x='Category', y='Value', hue='Series', ax=ax)
                elif chart_type == 'line_chart':
                    sns.lineplot(data=df, x='Category', y='Value', hue='Series', marker='o', ax=ax)
                
                ax.set_ylabel(data_source.get('title', di_set_id)) # Use the title for the y-axis label
                ax.set_xlabel(None)

            elif chart_type == 'pie_chart':
                # Handle both old format (labels/values) and new format (segments)
                if 'segments' in data:
                    # New format with segments
                    segments = data.get('segments', [])
                    if not segments:
                        print(f"  -> Skipping '{di_set_id}' (Pie chart data is empty).")
                        plt.close(fig)
                        continue
                    
                    labels = [seg.get('label', '') for seg in segments]
                    values = [seg.get('value', 0) for seg in segments]
                else:
                    # Old format with labels/values
                    labels = data.get('labels', [])
                    values = data.get('values', [])
                
                if not labels or not values:
                    print(f"  -> Skipping '{di_set_id}' (Pie chart data is empty).")
                    plt.close(fig)
                    continue
                
                # Wrap long labels to prevent them from overlapping
                wrapped_labels = [textwrap.fill(label, 15) for label in labels]
                ax.pie(values, labels=wrapped_labels, autopct='%1.1f%%', startangle=90)
                ax.axis('equal')

            # --- FINALIZATION AND SAVING ---
            ax.set_title(di_set_id, fontsize=16, weight='bold', pad=20) # Use di_set_id as the main title
            fig.tight_layout(rect=[0, 0, 1, 0.96]) # Adjust layout to make space for the title

            output_filename = f"{di_set_id}.png"
            output_path = Path(output_dir) / output_filename
            
            # Save with the same high DPI
            plt.savefig(output_path, dpi=300)
            plt.close(fig) # IMPORTANT: Close the figure to free up memory

        print("\n🎉 Chart generation complete!")

    except FileNotFoundError:
        print(f"❌ FATAL ERROR: The file was not found at '{json_file_path}'")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

# --- HOW TO RUN THE SCRIPT ---
if __name__ == "__main__":
    # Make sure your master JSON file is in the same directory as this script,
    # or provide the full path to it.
    MASTER_JSON_FILE = 'data/generated/master_questions/di_master_question_bank.json'
    
    generate_charts_from_master_file(MASTER_JSON_FILE)