import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
import google.generativeai as genai
import json
import zlib

def js_btoa(data):
    return base64.b64encode(data)

def pako_deflate(data):
    compress = zlib.compressobj(9, zlib.DEFLATED, 15, 8, zlib.Z_DEFAULT_STRATEGY)
    compressed_data = compress.compress(data)
    compressed_data += compress.flush()
    return compressed_data

def genPakoLink(graphMarkdown: str):
    jGraph = {"code": graphMarkdown, "mermaid": {"theme": "default"}}
    byteStr = json.dumps(jGraph).encode('utf-8')
    deflated = pako_deflate(byteStr)
    dEncode = js_btoa(deflated)
    link = 'http://mermaid.live/edit#pako:' + dEncode.decode('ascii')
    return link

# Gemini API Key - Replace with your actual key
genai.configure(api_key="AIzaSyC7zYaKkowJOivz8P2-rv5woJCkDkclczM")


def mm(graph):
    try:
        # Ensure the graph is properly encoded
        graphbytes = graph.encode("utf-8")
        base64_bytes = base64.b64encode(graphbytes)  # Use standard base64 encoding
        base64_string = base64_bytes.decode("ascii")
        
        # Use mermaid.ink URL with standard base64 encoding
        img_url = f"https://mermaid.ink/img/{base64_string}"
        
        # Download image and display
        response = requests.get(img_url, stream=True)
        response.raise_for_status()
        
        img = Image.open(BytesIO(response.content))
        st.image(img)
        
        # Provide download link
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        href = f'<a href="data:file/png;base64,{img_str}" download="mermaid_chart.png">Download Chart</a>'
        st.markdown(href, unsafe_allow_html=True)
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error generating or downloading chart: {e}")
        # Optional: Try to print or log the full traceback for debugging
        import traceback
        st.error(traceback.format_exc())


def generate_mermaid_from_gemini(project_status):
    try:
        # Use the generative model specifically for text generation
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Create a detailed prompt that guides the model to generate Mermaid chart code
        prompt = f"""Convert the following project status description into a Mermaid chart code (in the mermaid-js format) Example:
gantt
    dateFormat  YYYY-MM-DD
    axisFormat  %m-%d
    title Website Redesign Project

    section Planning & Design
    Planning :a1, 2024-01-08, 14d
    Design Mockups :after a1  , 14d
    Design Review :after a2  , 3d
    Design Approval : 2024-02-02

    section Development
    Frontend Development :after a4  , 25d
    Backend Development :after a4  , 24d
    API Integration : 2024-02-19, 10d
    Database Migration : 2024-02-12, 7d

    section Testing & Deployment
    Testing :after a5  , 11d
    Beta Testing : 2024-03-08, 7d
    Deployment Preparation :after a7 , 4d
    Deployment to Staging : 2024-03-22
    Final Deployment :after a8  , 4d
    Post-Launch Monitoring :after a9  , 7d
	Do NOT use the ```mermaid ... ``` strings in your reponse, return just the plain text
The chart should show the present data with a red line
        Ensure the chart is a clear, visual representation of the project status:
        
        {project_status}
        
        Please provide only the Mermaid chart code, without any additional explanation."""
        
        # Generate the response
        response = model.generate_content(prompt)
        
        # Extract the Mermaid code from the response
        mermaid_code = response.text.strip()
        
        return mermaid_code
    
    except Exception as e:
        st.error(f"Gemini API Error: {e}")
        return None

st.title("Project Status to Mermaid Chart")

project_status = st.text_area("Enter your project status description:")

if st.button("Generate Chart"):
    if project_status:
        mermaid_code = generate_mermaid_from_gemini(project_status)
        if mermaid_code:
            st.code(mermaid_code, language="mermaid") # Display the code
            mm(mermaid_code)
    else:
        st.warning("Please enter a project status description.")

if st.button("Generate link"):
    mermaid_code = generate_mermaid_from_gemini(project_status)
    if mermaid_code:
        mermaid_link = genPakoLink(mermaid_code)
        st.success("Here is the link for rendering on mermaid.live:")
        st.write(mermaid_link)
    else:
        st.warning("Please enter Mermaid code to generate the link")