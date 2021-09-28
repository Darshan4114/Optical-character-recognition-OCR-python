from django.shortcuts import render
from django.http import HttpResponse
from easyocr import Reader
import argparse
import cv2
import os
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes
from six import text_type
from .utils import cleanup_text
from django.views.decorators.csrf import csrf_exempt
import numpy as np
import json
import requests  # to get image from the web
import shutil  # to save it locally
# Create your views here.


@csrf_exempt
def ocr(request):
    if request.method == 'POST':
        post_data = json.loads(request.body.decode("utf-8"))
        file_url = post_data['fileURL']
        file_extension = post_data['fileExtension']
        # read_easy_ocr(file_url, file_extension)
        text_list = read_tesseract(file_url, file_extension)
        return HttpResponse(''.join(text_list))


def read_tesseract(file_url, file_extension):

    r = requests.get(file_url, stream=True)
    if r.status_code == 200:
        filename = "{}.png".format(os.getpid())
        text_list = []
        if(file_extension == 'jpg') or (file_extension == 'png'):
            nparr = np.fromstring(r.content, np.uint8)
            # cv2.IMREAD_COLOR in OpenCV 3.1
            img_np = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
            cv2.imwrite(filename, img_np)
            # load the image as a PIL/Pillow image, apply OCR, and then delete
            # the temporary file
            tessdata_dir_config = '--tessdata-dir "/usr/share/tesseract-ocr/4.00/tessdata"'
            text = pytesseract.image_to_string(Image.open(
                filename), lang="hin", config=tessdata_dir_config)
            os.remove(filename)
            text_list += text
            print(text)
        elif file_extension == 'pdf':
            images = convert_from_bytes(r.content, paths_only=True)
            print('img = ', images)
            counter = 0
            for image in images:
                image_name = 'image' + str(counter) + '.jpg'
                # Save images to the same folder
                image.save(image_name, 'JPEG')
                # Open the file as an image
                image_file = Image.open(image_name)
                # Use tesseract to extract the text from the image
                tessdata_dir_config = '--tessdata-dir "/usr/share/tesseract-ocr/4.00/tessdata"'
                string_contents = pytesseract.image_to_string(
                    image_file, lang="hin", config=tessdata_dir_config)
                # Print the contents to the console
                print(string_contents)
                text_list += string_contents
                counter += 1
                os.remove(image_name)
    return text_list


def read_easy_ocr(file_url, file_extension):
    reader = Reader(['en', 'hi'], True)
    text_list = []
    r = requests.get(file_url, stream=True)
    if r.status_code == 200:
        # Open the url image, set stream to True, this will return the stream content.
        if(file_extension == 'jpg') or (file_extension == 'png'):
            result = reader.readtext(r.content)
            for res in result:
                coords, text, probability = res
                text_list += text

        elif file_extension == 'pdf':
            images = convert_from_bytes(r.content)
            for image in images:
                result = reader.readtext(np.array(image))
                for res in result:
                    coords, text, probability = res
                    text_list += text

            print('Image sucessfully Downloaded: ', 'filename', )
            return HttpResponse(''.join(text_list))
    else:
        print('Image Couldn\'t be retreived')
        return HttpResponse('err')
