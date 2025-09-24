#!/usr/bin/env python3
"""
Plotly Installation Verification for FA-GPT
Simple test to verify Plotly and Kaleido are working correctly
"""

import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def verify_plotly_installation():
    """Verify Plotly installation with a basic scatter plot example."""
    
    print("🔍 Verifying Plotly Installation for FA-GPT")
    print("=" * 50)
    
    try:
        # Test 1: Basic imports
        print("✅ Successfully imported Plotly Express and Graph Objects")
        
        # Test 2: Create sample data
        sample_data = {
            'Document_Type': ['Firing_Table', 'Technical_Manual', 'Safety_Manual', 'Operator_Manual', 'Ammunition_Data'],
            'Processing_Time_Seconds': [12.5, 45.2, 18.7, 32.1, 8.9],
            'Accuracy_Score': [0.95, 0.88, 0.92, 0.85, 0.97],
            'Pages_Processed': [25, 120, 45, 80, 15]
        }
        
        df = pd.DataFrame(sample_data)
        print("✅ Created sample FA-GPT document processing data")
        
        # Test 3: Create interactive scatter plot
        fig = px.scatter(
            df, 
            x='Processing_Time_Seconds', 
            y='Accuracy_Score',
            size='Pages_Processed',
            color='Document_Type',
            title='FA-GPT Document Processing Performance',
            labels={
                'Processing_Time_Seconds': 'Processing Time (seconds)',
                'Accuracy_Score': 'Extraction Accuracy Score',
                'Pages_Processed': 'Pages Processed'
            },
            hover_data=['Pages_Processed']
        )
        
        # Customize the plot
        fig.update_layout(
            width=800,
            height=600,
            showlegend=True,
            template='plotly_white'
        )
        
        print("✅ Created interactive scatter plot successfully")
        
        # Test 4: Display the plot
        print("\n📊 Displaying interactive plot...")
        print("   (This should open in your default web browser)")
        fig.show()
        
        # Test 5: Test static export capability (Kaleido)
        try:
            static_file = f"/tmp/fagpt_plotly_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            fig.write_image(static_file, width=800, height=600)
            print(f"✅ Successfully exported static image to: {static_file}")
        except Exception as e:
            print(f"⚠️  Static image export test failed: {e}")
            print("   (This is optional - interactive plots will still work)")
        
        # Test 6: Create a simple bar chart for additional verification
        fig2 = px.bar(
            df,
            x='Document_Type',
            y='Accuracy_Score',
            title='FA-GPT Accuracy by Document Type',
            color='Accuracy_Score',
            color_continuous_scale='Viridis'
        )
        
        fig2.update_layout(
            xaxis_title='Document Type',
            yaxis_title='Accuracy Score',
            template='plotly_white'
        )
        
        print("✅ Created bar chart successfully")
        print("\n📊 Displaying bar chart...")
        fig2.show()
        
        print("\n🎉 All Plotly tests passed successfully!")
        print("\n✅ Plotly Features Verified:")
        print("   • Interactive scatter plots")
        print("   • Customizable styling and templates")
        print("   • Hover data and tooltips")
        print("   • Color mapping and sizing")
        print("   • Bar charts and other plot types")
        print("   • Static image export (if Kaleido working)")
        
        print("\n🚀 Ready for FA-GPT visualization integration!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("   Please check that Plotly is installed correctly")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    success = verify_plotly_installation()
    sys.exit(0 if success else 1)