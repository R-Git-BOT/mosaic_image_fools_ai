from asyncio.windows_events import NULL
from distutils.command.upload import upload
from turtle import up
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

import streamlit as st
import pathlib
from array import array
import os
from PIL import Image
import sys
import time
import cv2
import json
import glob
import shutil
import pandas as pd

# with open('secret.json') as f:
#     secret = json.load(f)

def detect_arg_score(imagepath):
    KEY = st.secrets.AzureApiKey.key
    ENDPOINT = st.secrets.AzureApiKey.endpoint
    
    local_image = open(imagepath, "rb")
    # remote_image_features = ["adult"]
    computervision_client = ComputerVisionClient(ENDPOINT, CognitiveServicesCredentials(KEY))
    # endpoint と key　があればAPIを使うことが出来る コピペ https://docs.microsoft.com/ja-jp/azure/cognitive-services/computer-vision/quickstarts-sdk/client-library?tabs=visual-studio&pivots=programming-language-python#authenticate-the-client
    detect_adult_results_remote = computervision_client.analyze_image_in_stream(local_image, ["adult"])

    return [detect_adult_results_remote.adult.adult_score * 100, detect_adult_results_remote.adult.racy_score * 100, detect_adult_results_remote.adult.gore_score * 100]

st.title('モザイクをかけてAIを騙せ！')

st.markdown('## Rule \n・画像を読み込ませると、AIくんがその画像を **"Adult" "Racy" "Gore"** の3項目で採点してくれるぞ')
st.markdown('・採点された画像にモザイク加工を施した画像で再採点するぞ')
st.markdown('・モザイク処理によって各要素の点数がどれだけ伸びたかで競ったり競わなかったりして下さい')
st.text(" \n")

uploaded_file = st.file_uploader('CHOOSE YOUR FIGHTER', type=['jpg', 'png'])

st.text(" \n")

placeholder = st

if uploaded_file is not None:
    # uploaded_fileが空っぽじゃなかったら通る
    img = Image.open(uploaded_file)
    img_path = f'img/{uploaded_file.name}'
    img.save(img_path)
    
    # st.image(img, caption='Your Fighter')

    normal_score = detect_arg_score(img_path)
    
    normal_score_df = pd.DataFrame(normal_score, index = ['adult','racy','gore'], columns = ['normal_score'])    

    # -------------

    local_image_cv = cv2.imread(img_path)

    def mosaic(src, ratio=0.01):
        small = cv2.resize(src, None, fx=ratio, fy=ratio, interpolation=cv2.INTER_NEAREST)
        return cv2.resize(small, src.shape[:2][::-1], interpolation=cv2.INTER_NEAREST)

    

    dst = mosaic(local_image_cv, 0.05)

    mosaic_stem = pathlib.Path(img_path).stem
    mosaic_suffix = pathlib.Path(img_path).suffix

    mosaic_image_path = 'img/'+ mosaic_stem + '_mosaic' +mosaic_suffix
    cv2.imwrite(mosaic_image_path, dst)
    # mosaic_image = open(mosaic_image_path, "rb")
    img_mosaic = Image.open(mosaic_image_path)
    # st.image(img_mosaic, caption='Mosaic of Your Fighter')

    remote_image_features = ["adult"]
    # Call API with URL and features

    mosaic_score = detect_arg_score(mosaic_image_path)

    mosaic_score_df = pd.DataFrame(mosaic_score, index = ['adult','racy','gore'], columns = ['mosaic_score'])

    img1, img2 = st.columns(2)
    with img1:
        st.image(img, caption='Your Fighter')
    with img2:
        st.image(img_mosaic, caption='Mosaic of Your Fighter')

    normal_adult = normal_score_df.at['adult', 'normal_score']
    normal_racy = normal_score_df.at['racy', 'normal_score']
    normal_gore = normal_score_df.at['gore', 'normal_score']

    mosaic_adult = mosaic_score_df.at['adult', 'mosaic_score']
    mosaic_racy = mosaic_score_df.at['racy', 'mosaic_score']
    mosaic_gore = mosaic_score_df.at['gore', 'mosaic_score']

    st.text(" \n")
    col1, col2, col3 = st.columns(3)
    col1.metric("Adult Score", value = round(10000*(mosaic_adult - normal_adult)))
    col2.metric("Racy Score", value = round(10000*(mosaic_racy - normal_racy)))
    col3.metric("Gore Score", value = round(10000*(mosaic_gore - normal_gore)))

if uploaded_file is None:
    target = glob.glob(r"img/*.png") + glob.glob(r"img/*.jpg")
    if len(target) > 0:
        for file in target:
            os.remove(file)