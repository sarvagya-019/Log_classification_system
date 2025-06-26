import pandas as pd
import matplotlib.pyplot as plt
import os
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
from classify import classify
app = FastAPI()
# ─────────────────────────────────────────────
@app.post("/classify/")
async def classify_logs(file: UploadFile):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV.")
    
    try:
        # Read the uploaded CSV
        df = pd.read_csv(file.file)
        if "source" not in df.columns or "log_message" not in df.columns:
            raise HTTPException(status_code=400, detail="CSV must contain 'source' and 'log_message' columns.")

        # Perform classification
        df["target_label"] = classify(list(zip(df["source"], df["log_message"])))

        # Save the modified file
        os.makedirs("resources", exist_ok=True)
        output_file = "resources/output.csv"
        df.to_csv(output_file, index=False)
        return FileResponse(output_file, media_type='text/csv')
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        file.file.close()

# ─────────────────────────────────────────────
@app.get("/plot/")
def generate_plot():
    try:
        df = pd.read_csv("resources/output.csv")

        if "source" not in df.columns:
            raise HTTPException(status_code=400, detail="'source' column not found in output.csv")

        # Count log messages by source
        source_counts = df['source'].value_counts()

        # Create a bar chart
        plt.figure(figsize=(10, 6))
        plt.bar(source_counts.index, source_counts.values, color='mediumseagreen')
        plt.xlabel("Source System")
        plt.ylabel("Log Count")
        plt.title("Log Messages per Source")
        plt.xticks(rotation=45)
        plt.tight_layout()

        os.makedirs("resources", exist_ok=True)
        plot_path = "resources/bar_plot.png"
        plt.savefig(plot_path)
        plt.close()

        return FileResponse(plot_path, media_type="image/png")
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Output file not found. Please classify a file first.")
