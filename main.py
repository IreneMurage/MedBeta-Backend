from app import create_app
import os
from dotenv import load_dotenv

load_dotenv()
app=create_app()


@app.route("/")
def Home():
    return "MedBeta Fullstack is working"

if __name__=="__main__":
    app.run(debug=True)

