# -*- coding: utf-8 -*-
"""Untitled6.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1dzTDJ4AQYO2Y2ecypb3grjIjNN8Qmq3O
"""

from google.colab import files
!pip install -q kaggle
uploaded = files.upload()

!mkdir -p ~/.kaggle
!cp kaggle.json ~/.kaggle/
!chmod 600 ~/.kaggle/kaggle.json
!kaggle datasets download -d ashishsaxena2209/animal-image-datasetdog-cat-and-panda

!unzip animal-image-datasetdog-cat-and-panda.zip

import os
import shutil

dir_utama = os.path.join('/content/animals')

ignore_dir = ['images', 'animals']

for dir in ignore_dir:
  path = os.path.join(dir_utama, dir)
  shutil.rmtree(path)

print(os.listdir(dir_utama))

# import os
# import cv2
import requests
import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt

from PIL import Image
from io import BytesIO
# from tqdm.notebook import tqdm
from sklearn.model_selection import train_test_split

from tensorflow.keras import applications, optimizers
# from tensorflow.keras.models import Sequential, Model, load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator

tf.device('/device:GPU:0')

fig, ax = plt.subplots(2, 3, figsize=(25,15))
fig.suptitle("Menampilkan satu gambar acak setiap kategori", fontsize=24)
data_dir = "/content/animals/"
animals_sorted = sorted(os.listdir(data_dir))
animal_id = 0
for i in range(2):
  for j in range(5):
    try:
      animal_selected = animals_sorted[animal_id] 
      animal_id += 1
    except:
      break
    if animal_selected == '.TEMP':
        continue
    animal_selected_images = os.listdir(os.path.join(data_dir,animal_selected))
    animal_selected_random = np.random.choice(animal_selected_images)
    img = plt.imread(os.path.join(data_dir,animal_selected, animal_selected_random))
    ax[i][j].imshow(img)
    ax[i][j].set_title(animal_selected, pad = 3, fontsize=22)
    
plt.setp(ax, xticks=[],yticks=[])
plt.tight_layout()

kategori_dict = {"cats": "cats", "panda": "panda", "dogs": "dogs"}

# Membuat Dataframe
foldernames = os.listdir('animals/')
path_get, path_not, kategori_get, kategori_not = [], [], [], []

for i, folder in enumerate(foldernames):
    filenames = os.listdir("animals/" + folder);
    count = 0
    for file in filenames:
        if count < 1000: # Mengambil 3000 data max tiap kategori
            path_get.append("animals/" + folder + "/" + file)
            kategori_get.append(kategori_dict[folder])
        count += 1

df = pd.DataFrame({'path':path_get, 'kategori':kategori_get})
train, test = train_test_split(df, test_size=0.2, random_state = 0)

train_gen = ImageDataGenerator(rescale=1./255,
  shear_range=0.3,
  zoom_range=0.3,
  horizontal_flip=True,
  rotation_range=35, 
  width_shift_range=0.15,
  height_shift_range=0.15,
  samplewise_center = True,
)

test_gen = ImageDataGenerator(rescale=1./255, samplewise_center = True)

train_flow = train_gen.flow_from_dataframe(
    train, x_col = 'path', 
    y_col = 'kategori', 
    target_size=(224, 224),  
    validate_filenames = False,
    class_mode='categorical', 
    batch_size=64)
test_flow = test_gen.flow_from_dataframe(
    test, x_col = 'path', 
    y_col = 'kategori', 
    target_size=(224, 224), 
    validate_filenames = False,
    class_mode='categorical', 
    batch_size=64)

model = tf.keras.models.Sequential([
                                    
  applications.ResNet152V2(weights="imagenet", include_top=False, 
                           input_tensor=tf.keras.layers.Input(shape=(224, 224, 3))),

  tf.keras.layers.MaxPooling2D(pool_size=(6, 6)),

  tf.keras.layers.Convolution2D(2048, 1, 1),
  tf.keras.layers.Activation('relu'),
  tf.keras.layers.MaxPooling2D(pool_size=(1, 1)),
  
  tf.keras.layers.Convolution2D(1024, 1, 1),
  tf.keras.layers.Activation('relu'),
  tf.keras.layers.MaxPooling2D(pool_size=(1,1)),

  tf.keras.layers.Convolution2D(512, 1, 1),
  tf.keras.layers.Activation('relu'),
  tf.keras.layers.MaxPooling2D(pool_size=(1,1)),

  tf.keras.layers.Convolution2D(256, 1, 1),
  tf.keras.layers.Activation('relu'),
  tf.keras.layers.MaxPooling2D(pool_size=(1,1)),

  tf.keras.layers.Convolution2D(128, 1, 1),
  tf.keras.layers.Activation('relu'),
  tf.keras.layers.MaxPooling2D(pool_size=(1,1)),

  tf.keras.layers.Convolution2D(64, 1, 1),
  tf.keras.layers.Activation('relu'),
  tf.keras.layers.MaxPooling2D(pool_size=(1,1)),

  tf.keras.layers.Flatten(), 
  tf.keras.layers.Dropout(0.2),
  tf.keras.layers.Dense(256, activation='relu'),
  tf.keras.layers.Dropout(0.2),
  tf.keras.layers.Dense(3, activation='softmax')  
])
model.layers[0].trainable = False

def scheduler(epoch, lr):
  if epoch < 5:
    return lr
  else:
    return lr * tf.math.exp(-0.1)

lr_schedule = tf.keras.callbacks.LearningRateScheduler(scheduler, verbose=1)
tb_callback = tf.keras.callbacks.TensorBoard(
    log_dir='logs', histogram_freq=0, write_graph=True, write_images=False,
    update_freq='epoch', embeddings_freq=0,
    embeddings_metadata=None
)

model.compile(loss = 'categorical_crossentropy', optimizer = optimizers.SGD(lr=1e-3, momentum=0.9), 
              metrics = ['accuracy'])
model.summary()

with tf.device("/device:GPU:0"):
  history = model.fit_generator(train_flow, epochs = 15, validation_data = test_flow, 
                                steps_per_epoch=train.shape[0]//224, validation_steps=test.shape[0]//224,
                                callbacks=[lr_schedule, tb_callback])

# Evaluasi Model
eval_model = model.evaluate_generator(test_flow, verbose=1)
print('Loss : {} \nAcc : {}'.format(eval_model[0]*100, eval_model[1]*100))

# Commented out IPython magic to ensure Python compatibility.
# Load the TensorBoard notebook extension.
# %load_ext tensorboard
# %tensorboard --logdir logs

# Konversi model.
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

with tf.io.gfile.GFile('model.tflite', 'wb') as f:
  f.write(tflite_model)