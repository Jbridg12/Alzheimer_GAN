# -*- coding: utf-8 -*-
"""Classifier.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1HxgnLCIzbwCur1aZ0ydNpABSySMwIQ4E

# Initialize Notebook
"""

import tensorflow as tf
import numpy as np
from tensorflow.keras import layers
from tensorflow.keras.utils import image_dataset_from_directory
from sklearn.preprocessing import OneHotEncoder
import matplotlib.pyplot as plt
import os
from os import listdir
from os.path import join, isdir
from os import listdir
from PIL import Image
from time import sleep

tf.config.run_functions_eagerly(True)

os.environ['KAGGLE_CONFIG_DIR'] = "/content/gdrive/MyDrive/"

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/gdrive/MyDrive/

# Extract trained GAN - uncomment as necessary
# from zipfile import ZipFile
# with ZipFile('gen1.zip', 'r') as zipper:
#  zipper.extractall()

"""Note: Operates under the assumption that dataset is in home directory of google drive.

# Loading Dataset
"""


class_name = np.array([f for f in listdir('./Dataset') if isdir(join('./Dataset', f))])
n_classes = len(class_name)
print(n_classes)

# Checks for corrupt files in dataset
# From https://opensource.com/article/17/2/python-tricks-artists

bad_files = []
for dir in listdir('Dataset/'):
  for file in listdir('Dataset/'+dir):
    # print(file)
    # break
    if file.endswith('.jpg'):
      try:
        img = Image.open('Dataset/'+dir+'/'+file)
        img.verify()
      except (IOError, SyntaxError) as e:
        print('Bad file:', file)
        path = 'Dataset/'+dir+'/'+file
        bad_files.append(path)

# Removes corrupted files
print(len(bad_files))
for file in bad_files:
  os.remove(file)

# For replicable results
SEED = 0
# Size of Latent Input
noise_dim = 100
num_examples_to_generate = 16
# Size of the images is (128,128)
IMAGE_SIZE = (128, 128)
# Default batch size
BATCH_SIZE = 32
# Images are grayscale
COLOR_MODE = "grayscale"

"""# Generate Images"""

# Clear any previously generated images
from os import listdir
from PIL import Image

def remove_gen_images():
  count = 0
  for dir in listdir('Dataset/'):
    for file in listdir('Dataset/'+dir):
      if 'Gen' in file:
        count += 1
        os.remove('Dataset/'+dir+'/'+file)

  print(f'Removed {count} files.')

remove_gen_images()

"""### Generate One Image"""

# Load trained model
generator = tf.keras.models.load_model('./gen1')

def get_image(target, training=False):
  test_noise = tf.random.normal([1, noise_dim]).numpy()
  tst_in = []
  tst_in.append(np.append(test_noise[0], target))
  test_input = tf.convert_to_tensor(np.array(tst_in))

  # Generate images
  img = generator(test_input, training=training)

  return img

gen_img = get_image(1, training=False)
plt.clf()
plt.imshow(gen_img[0,:,:,0], cmap='gray')

"""### Generate Multiple Images"""

remove_gen_images()

"""Generates 20 images and loads them into corresponding target files."""

# Generates a given number of images
num_images = 800
target_names = np.array([f for f in listdir('./Dataset') if isdir(join('./Dataset', f))])
print(target_names)

num_targets = np.random.randint(0, 4, num_images)
for i in range(num_images):
  target = num_targets[i]

  new_image = get_image(target, training=False)

  # Plot and save images
  plt.clf()
  plt.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
  plt.imshow(new_image[0,:,:,0], cmap='gray')
  plt.savefig('Dataset/'+target_names[target]+'/Gen_'+str(i)+'.jpg')

"""Give time for images to be saved and loaded into the drive."""

sleep(20)

"""Load training data that includes GAN generated images."""

# If cells run sequentially should now contain true and generated images
gan_train_data = tf.keras.preprocessing.image_dataset_from_directory(
    'Dataset/',
    validation_split=0.2,
    subset="training",
    label_mode='categorical',
    seed=SEED,
    color_mode=COLOR_MODE,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE
)

"""Load testing data that includes GAN generated images."""

# If cells run sequentially should now contain true and generated images
gan_test_data = tf.keras.preprocessing.image_dataset_from_directory(
    'Dataset/',
    validation_split=0.2,
    subset="validation",
    label_mode='categorical',
    seed=SEED,
    color_mode=COLOR_MODE,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE
)

"""# Classifiers"""

# Epoch-Loss Plots

def epoch_loss(hist, axis=None):
  plt.figure()
  plt.title('Epoch-Loss')
  plt.xlabel('Epoch')
  plt.ylabel('Loss')

  if axis is not None:
    plt.ylim(0, axis)

  plot_loss = hist.history['loss']
  val_loss = hist.history['val_loss']
  plt.xticks(np.arange(0, len(plot_loss)+2, 2))
  plt.plot(range(len(plot_loss)), plot_loss)
  plt.plot(range(len(plot_loss)), val_loss)
  plt.legend(['Loss', 'Val Loss'])
  plt.show()

def acc_loss(hist, axis=None):
  plot_loss = hist.history['loss']
  plot_acc = hist.history['accuracy']

  val_loss = hist.history['val_loss']
  val_acc = hist.history['val_accuracy']

  plt.figure()
  if axis is not None:
    plt.ylim(0, axis)
  plt.title('Accuracy-Loss')
  plt.xlabel('Accuracy')
  plt.ylabel('Loss')
  plt.plot(plot_acc, plot_loss)
  plt.plot(val_acc, val_loss)
  plt.legend(['Acc-Loss', 'Val Acc-Val Loss'])
  plt.show()

def epoch_acc(hist, axis=None):
  plot_acc = hist.history['accuracy']
  val_acc = hist.history['val_accuracy']

  plt.figure()
  if axis is not None:
    plt.ylim(0, axis)
  plt.title('Epoch-Accuracy')
  plt.xlabel('Epoch')
  plt.ylabel('Accuracy')
  plt.xticks(np.arange(0, len(plot_acc)+2, 2))
  plt.plot(range(len(plot_acc)), plot_acc)
  plt.plot(range(len(plot_acc)), val_acc)
  plt.legend(['Accuracy', 'Val Accuracy'])
  plt.show()

"""### Classic Classifier"""

def train_cmodel(gan_train_data, gan_test_data, epochs):
  # Basic classifier taken from https://www.tensorflow.org/tutorials/load_data/images for testing
  cmodel = tf.keras.Sequential()
  cmodel.add(layers.Conv2D(32, 3, activation='relu'))
  cmodel.add(layers.MaxPool2D())
  cmodel.add(layers.Conv2D(64, 3, activation='relu'))
  cmodel.add(layers.MaxPool2D())
  cmodel.add(layers.Conv2D(32, 3, activation='relu'))
  cmodel.add(layers.MaxPool2D())
  cmodel.add(layers.Flatten())
  cmodel.add(layers.Dense(128, activation='relu'))
  cmodel.add(layers.Dense(4, 'softmax'))

  cmodel.compile(optimizer='adam',
                loss=tf.losses.CategoricalCrossentropy(),
                metrics=['accuracy'])

  cmodel.fit(gan_train_data, validation_data=gan_test_data, epochs=epochs)

  return cmodel

classic_model = train_cmodel(gan_train_data, gan_test_data, 20)

tf.keras.utils.plot_model(classic_model, show_shapes=True, dpi=64)

epoch_loss(classic_model.history)
acc_loss(classic_model.history)
epoch_acc(classic_model.history)

"""### Single Convolution Layer Classifier"""

def train_conv_model(gan_train_data, gan_test_data, epochs):
  dmodel = tf.keras.Sequential()
  dmodel.add(layers.Conv2D(32, 3))

  dmodel.add(layers.Flatten())
  dmodel.add(layers.Activation('relu'))
  dmodel.add(layers.Dense(4, 'softmax'))

  dmodel.compile(optimizer='adam',
                loss=tf.losses.CategoricalCrossentropy(),
                metrics=['accuracy'])
  dmodel.fit(gan_train_data, validation_data=gan_test_data,epochs=epochs)

  return dmodel

conv_model = train_conv_model(gan_train_data, gan_test_data, 20)

tf.keras.utils.plot_model(conv_model, show_shapes=True, dpi=64)

epoch_loss(conv_model.history, 5)
acc_loss(conv_model.history)
epoch_acc(conv_model.history)

# Generates a given number of images
num_images = 50
target_names = np.array([f for f in listdir('./Dataset') if isdir(join('./Dataset', f))])
print(target_names)

num_targets = np.random.randint(0, 4, num_images)
print(num_targets)
img_list = []
for i in range(num_images):
  target = num_targets[i]

  gen_image = get_image(target, training=False)
  img_list.append(gen_image)

  pred = classic_model.predict(gen_image)
  print(pred)
  print(f'Predicted: {np.argmax(pred)}  |   True: {target}')

num_images = 20
target_names = np.array([f for f in listdir('./Dataset') if isdir(join('./Dataset', f))])
print(target_names)

num_targets = np.random.randint(0, 4, num_images)
for i in range(num_images):
  target = num_targets[i]

  new_image = get_image(target, training=False)

  pred_val = classic_model.predict(new_image)

  print(f'Predicted: {np.argmax(pred_val)}   | Actual: {target}')

plt.figure(figsize=(10, 10))
for i in range(9):
  ax = plt.subplot(3, 3, i + 1)
  plt.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
  plt.imshow(img_list[i][0,:,:,0], cmap='gray')