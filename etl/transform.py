import pandas as pd

def transform_data(data, columns):
    df = pd.DataFrame(data, columns=columns)
    # Add any transformation logic here (e.g., cleaning, aggregation)
    df['new_column'] = df['existing_column'] * 2  # Example transformation
    return df