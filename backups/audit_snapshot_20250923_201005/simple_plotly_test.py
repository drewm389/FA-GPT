#!/usr/bin/env python3
"""
Simple Plotly Verification Snippet for FA-GPT
Quick test to verify Plotly Express is working correctly
"""

import plotly.express as px
import pandas as pd

# Create sample data
data = {
    'x': [1, 2, 3, 4, 5],
    'y': [2, 4, 1, 5, 3],
    'category': ['A', 'B', 'A', 'B', 'A']
}

df = pd.DataFrame(data)

# Create basic scatter plot
fig = px.scatter(df, x='x', y='y', color='category', title='FA-GPT Plotly Verification')

# Display the plot
fig.show()

print("✅ Plotly is working correctly!")
print("🎯 Interactive plot should have opened in your browser")