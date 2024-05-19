import streamlit as st
import pandas as pd
from PIL import Image
import subprocess
import os
import base64
import pickle

#import subprocess
import os
import streamlit as st

def desc_calc():
    jar_path = "./PaDEL-Descriptor/PaDEL-Descriptor.jar"
    xml_path = "./PaDEL-Descriptor/PubchemFingerprinter.xml"
    input_file = './molecule.smi'
    output_file = './descriptors_output.csv'
    
    # Constructing the bash command
    bash_command = (
        f"java -Xms1G -Xmx1G -Djava.awt.headless=true "
        f"-jar {jar_path} "
        f"-removesalt -standardizenitro -fingerprints "
        f"-descriptortypes {xml_path} "
        f"-dir ./ -file {output_file}"
    )
    
    try:
        # Print the command
        st.write(f"Running command")

        # Running the bash command
        result = subprocess.run(bash_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Print the standard output and error
        st.write(f"Standard Output:\n{result.stdout}")
        st.write(f"Error Output:\n{result.stderr}")
        
        # Check if the process exited successfully
        if result.returncode != 0:
            st.error(f"PaDEL-Descriptor error: {result.stderr}")
            return
        
        # Check if the output file exists and is not empty
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            st.write("Descriptor calculation completed successfully.")
        else:
            st.error("Error: Descriptor calculation failed. Output file not found or is empty.")
    
    except Exception as e:
        st.error(f"Error occurred during descriptor calculation: {str(e)}")


# File download function
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="prediction.csv">Download Predictions</a>'
    return href

# Model building function
def build_model(input_data):
    load_model = pickle.load(open('./insulin_model.pkl', 'rb'))
    prediction = load_model.predict(input_data)
    st.header('**Prediction output**')
    prediction_output = pd.Series(prediction, name='pIC50')
    molecule_names = input_data.index  # Assuming input_data has molecule names as index
    df = pd.DataFrame({'molecule_name': molecule_names, 'pIC50': prediction_output})
    st.write(df)
    st.markdown(filedownload(df), unsafe_allow_html=True)

# Streamlit page configuration
st.markdown("""
<style>
#bpair-text {
  position: absolute;
  top: 0px;
  left: 0px;
  font-weight: bold;
  font-size: 29px;
  color: #7A55FF;
  padding: 10px;
  margin-bottom: 50px;
}
</style>
<div id="bpair-text">BPAIR</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style='font-weight:bold; color:black; margin-top: 50px; font-size: 30px;'>Bioactivity Prediction App (Insulin Receptor)</div>
---
""", unsafe_allow_html=True)

image = Image.open('./ins.webp')
st.image(image, use_column_width=True)

st.markdown("""
<span style='color:#7A55FF; font-weight:bold; font-size: 22px;'>Bioactivity Prediction App (Insulin Receptor) :</span>
---
""", unsafe_allow_html=True)

st.markdown("""
<span style='font-size: 20px; font-weight: normal;'>Cette application fournit des estimations sur l'efficacité potentielle de diverses substances pour inhiber le récepteur de l'insuline. Cette information pourrait s'avérer précieuse dans le développement de nouveaux médicaments.</span>
---
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload your input file", type=['txt'])
st.markdown("[Example input file](https://raw.githubusercontent.com/dataprofessor/bioactivity-prediction-app/main/example_acetylcholinesterase.txt)")


if st.button('Predict'):
    if uploaded_file is not None:
        load_data = pd.read_table(uploaded_file, sep=r'\s+', header=None, names=['Structure', 'Identifier'])
         # Set 'Identifier' column as index to use molecule names as index
        
        
        load_data.to_csv('molecule.smi', sep='\t', header=False, index=False)

        st.header('**Original input data**')
        st.write(load_data)

        with st.spinner("Calculating descriptors..."):
            desc_calc()

        # Debug: Check if the descriptor file is created and its contents
        if os.path.exists(r'.\descriptors_output.csv'):
            st.write("Descriptor file found.")
            desc = pd.read_csv(r'.\descriptors_output.csv')
            
        else:
            st.error("Descriptor file not found. Descriptor calculation may have failed.")

        st.header('**Calculated molecular descriptors**')
        desc = pd.read_csv(r'.\descriptors_output.csv')
        st.write(desc.shape)
        st.write(desc.head())  # Display the first few rows of the descriptor file for debugging

        st.header('**Subset of descriptors from previously built models**')
        try:
            Xlist = list(pd.read_csv(r'.\descriptor_list.csv').columns)
            desc_subset = desc[Xlist]
            st.write(desc_subset)
            st.write(desc_subset.shape)
        except Exception as e:
            st.error(f"Error creating subset of descriptors: {str(e)}")

        build_model(desc_subset)
    else:
        st.warning("Please upload a file before predicting.")

st.sidebar.header('**Informations sur le récepteur de l\'insuline:**')
st.sidebar.write("""
Le récepteur de l'insuline joue un rôle crucial dans la régulation des niveaux de sucre dans le sang. Lorsque l'insuline se lie à son récepteur correspondant à la surface des cellules, cela déclenche une série de réponses cellulaires visant à faciliter l'absorption, le stockage et l'utilisation du glucose. Ce processus complexe garantit que les cellules reçoivent un approvisionnement constant en énergie, maintenant ainsi des niveaux de sucre dans le sang stables, essentiels pour diverses fonctions métaboliques.

Notre application web facilite la prédiction de la bioactivité sur la base de données moléculaires fournies en entrée. Les utilisateurs peuvent télécharger des données relatives aux structures chimiques, aux descripteurs moléculaires et aux valeurs de bioactivité expérimentales ou prédites. Une fois ces informations fournies, notre application calcule les descripteurs moléculaires et utilise des modèles d'apprentissage automatique pour prédire la bioactivité des molécules. Ces prédictions fournissent des informations précieuses pour prioriser les molécules en vue de validations expérimentales supplémentaires ou de découvertes de médicaments.
""")