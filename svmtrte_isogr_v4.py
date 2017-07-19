import os
os.environ['CUDA_VISIBLE_DEVICES'] = '1'
import io
import sys
import numpy as np
import tensorflow as tf
import tensorlayer as tl
import inputs as data
import c3d_biclstm_fpooling as net 
import time
from datetime import datetime
import threading
from sklearn import svm

seq_len = 32
batch_size = 8

num_classes = 249
dataset_name = 'isogr'
model_prefix='/raid/gmzhu/tensorflow/gestureness3'

curtime = '%s' % datetime.now()
d = curtime.split(' ')[0]
t = curtime.split(' ')[1]
strtime = '%s%s%s-%s%s%s' %(d.split('-')[0],d.split('-')[1],d.split('-')[2], 
                            t.split(':')[0],t.split(':')[1],t.split(':')[2])

x = tf.placeholder(tf.float32, [batch_size, seq_len, 112, 112, 3], name='x')
y = tf.placeholder(tf.int32, shape=[batch_size, ], name='y')
  
sess = tf.InteractiveSession()

feature_layer, networks = net.c3d_biclstm(x, num_classes, False, False)
feature_stfp = feature_layer.outputs 
network_pred = tf.nn.softmax(networks.outputs)
network_y_op = tf.argmax(tf.nn.softmax(networks.outputs),1)
network_accu = tf.reduce_mean(tf.cast(tf.equal(tf.cast(network_y_op, tf.int32), y), tf.float32))
  
sess.run(tf.initialize_all_variables())

#####################################################################################
######            1. Extracting features of the training dataset               ######
#####################################################################################
# RGB
training_datalist = '/ssd/dataset/IsoGD_Image/train_rgb_list.txt'
X_train,y_train = data.load_video_list(training_datalist)
X_tridx = np.asarray(np.arange(0, len(y_train)), dtype=np.int32)
y_train  = np.asarray(y_train, dtype=np.int32)
training_feats = np.zeros((len(y_train), 12288), dtype=np.float32)
training_label = np.zeros((len(y_train), 1), dtype=np.int32)
load_params = tl.files.load_npz(name='%s/fpooling_avg_ft/isogr_rgb_birnn_model_epoch_10.npz'%(model_prefix))
tl.files.assign_params(sess, load_params, networks)
#networks.print_params(True)
train_iterations = 0
print '%s: extracting rgb training features' % datetime.now()
for X_indices, y_label_t in tl.iterate.minibatches(X_tridx, 
                                                   y_train, 
                                                   batch_size, 
                                                   shuffle=False):
  # Read data for each batch      
  image_path = []
  image_fcnt = []
  image_olen = []
  is_training = []
  for data_a in range(batch_size):
    X_index_a = X_indices[data_a]
    key_str = '%06d' % X_index_a
    image_path.append(X_train[key_str]['videopath'])
    image_fcnt.append(X_train[key_str]['framecnt'])
    image_olen.append(seq_len)
    is_training.append(False) # Testing
    image_info = zip(image_path,image_fcnt,image_olen,is_training)
  X_data_t = tl.prepro.threading_data([_ for _ in image_info], 
                                      data.prepare_isogr_rgb_data)
  feed_dict = {x: X_data_t, y: y_label_t}
  dp_dict = tl.utils.dict_to_one(networks.all_drop)
  feed_dict.update(dp_dict)
  _,feat_value = sess.run([network_pred, feature_stfp], feed_dict=feed_dict)
  training_feats[train_iterations*batch_size:(train_iterations+1)*batch_size,0:4096]=feat_value
  training_label[train_iterations*batch_size:(train_iterations+1)*batch_size,0]=y_label_t
  train_iterations = train_iterations + 1

# Depth
training_datalist = '/ssd/dataset/IsoGD_Image/train_depth_list.txt'
X_train,y_train = data.load_video_list(training_datalist)
X_tridx = np.asarray(np.arange(0, len(y_train)), dtype=np.int32)
y_train  = np.asarray(y_train, dtype=np.int32)
load_params = tl.files.load_npz(name='%s/fpooling_avg_ft/isogr_depth_birnn_model_epoch_10.npz'%(model_prefix))
tl.files.assign_params(sess, load_params, networks)
#networks.print_params(True)
train_iterations = 0
print '%s: extracting depth training features' % datetime.now()
for X_indices, y_label_t in tl.iterate.minibatches(X_tridx, 
                                                   y_train, 
                                                   batch_size, 
                                                   shuffle=False):
  # Read data for each batch      
  image_path = []
  image_fcnt = []
  image_olen = []
  is_training = []
  for data_a in range(batch_size):
    X_index_a = X_indices[data_a]
    key_str = '%06d' % X_index_a
    image_path.append(X_train[key_str]['videopath'])
    image_fcnt.append(X_train[key_str]['framecnt'])
    image_olen.append(seq_len)
    is_training.append(False) # Testing
    image_info = zip(image_path,image_fcnt,image_olen,is_training)
  X_data_t = tl.prepro.threading_data([_ for _ in image_info], 
                                      data.prepare_isogr_depth_data)
  feed_dict = {x: X_data_t, y: y_label_t}
  dp_dict = tl.utils.dict_to_one(networks.all_drop)
  feed_dict.update(dp_dict)
  _,feat_value = sess.run([network_pred, feature_stfp], feed_dict=feed_dict)
  training_feats[train_iterations*batch_size:(train_iterations+1)*batch_size,4096:8192]=feat_value
  train_iterations = train_iterations + 1

# Flow
training_datalist = '/ssd/dataset/IsoGD_Image/train_flow_list.txt'
X_train,y_train = data.load_video_list(training_datalist)
X_tridx = np.asarray(np.arange(0, len(y_train)), dtype=np.int32)
y_train  = np.asarray(y_train, dtype=np.int32)
load_params = tl.files.load_npz(name='%s/fpooling_avg_ft/isogr_flow_birnn_model_epoch_10.npz'%(model_prefix))
tl.files.assign_params(sess, load_params, networks)
#networks.print_params(True)
train_iterations = 0
print '%s: extracting flow training features' % datetime.now()
for X_indices, y_label_t in tl.iterate.minibatches(X_tridx, 
                                                   y_train, 
                                                   batch_size, 
                                                   shuffle=False):
  # Read data for each batch      
  image_path = []
  image_fcnt = []
  image_olen = []
  is_training = []
  for data_a in range(batch_size):
    X_index_a = X_indices[data_a]
    key_str = '%06d' % X_index_a
    image_path.append(X_train[key_str]['videopath'])
    image_fcnt.append(X_train[key_str]['framecnt'])
    image_olen.append(seq_len)
    is_training.append(False) # Testing
    image_info = zip(image_path,image_fcnt,image_olen,is_training)
  X_data_t = tl.prepro.threading_data([_ for _ in image_info], 
                                      data.prepare_isogr_flow_data)
  feed_dict = {x: X_data_t, y: y_label_t}
  dp_dict = tl.utils.dict_to_one(networks.all_drop)
  feed_dict.update(dp_dict)
  _,feat_value = sess.run([network_pred, feature_stfp], feed_dict=feed_dict)
  training_feats[train_iterations*batch_size:(train_iterations+1)*batch_size,8192:12288]=feat_value
  train_iterations = train_iterations + 1

#####################################################################################
######            2. Extracting features of the validitng dataset               ######
#####################################################################################
# RGB
testing_datalist = '/ssd/dataset/IsoGD_Image/valid_rgb_list.txt'
X_test,y_test = data.load_video_list(testing_datalist)
X_teidx = np.asarray(np.arange(0, len(y_test)), dtype=np.int32)
y_test  = np.asarray(y_test, dtype=np.int32)
testing_feats = np.zeros((len(y_test), 12288), dtype=np.float32)
testing_label = np.zeros((len(y_test), 1), dtype=np.float32)
rgb_prediction = np.zeros((len(y_test),num_classes), dtype=np.float32)
load_params = tl.files.load_npz(name='%s/fpooling_avg_ft/isogr_rgb_birnn_model_epoch_10.npz'%(model_prefix))
tl.files.assign_params(sess, load_params, networks)
#networks.print_params(True)
average_accuracy = 0.0
test_iterations = 0
print '%s: rgb testing' % datetime.now()
for X_indices, y_label_t in tl.iterate.minibatches(X_teidx, 
                                                   y_test, 
                                                   batch_size, 
                                                   shuffle=False):
  # Read data for each batch      
  image_path = []
  image_fcnt = []
  image_olen = []
  is_training = []
  for data_a in range(batch_size):
    X_index_a = X_indices[data_a]
    key_str = '%06d' % X_index_a
    image_path.append(X_test[key_str]['videopath'])
    image_fcnt.append(X_test[key_str]['framecnt'])
    image_olen.append(seq_len)
    is_training.append(False) # Testing
    image_info = zip(image_path,image_fcnt,image_olen,is_training)
  X_data_t = tl.prepro.threading_data([_ for _ in image_info], 
                                      data.prepare_isogr_rgb_data)
  feed_dict = {x: X_data_t, y: y_label_t}
  dp_dict = tl.utils.dict_to_one(networks.all_drop)
  feed_dict.update(dp_dict)
  predict_value,accu_value,feat_value = sess.run([network_pred, network_accu, feature_stfp], feed_dict=feed_dict)
  rgb_prediction[test_iterations*batch_size:(test_iterations+1)*batch_size,:]=predict_value
  testing_feats[test_iterations*batch_size:(test_iterations+1)*batch_size,0:4096]=feat_value
  testing_label[test_iterations*batch_size:(test_iterations+1)*batch_size,0]=y_label_t
  average_accuracy = average_accuracy + accu_value
  test_iterations = test_iterations + 1
average_accuracy = average_accuracy / test_iterations
format_str = ('%s: rgb average_accuracy = %.6f')
print (format_str % (datetime.now(), average_accuracy))

# Depth
testing_datalist = '/ssd/dataset/IsoGD_Image/valid_depth_list.txt'
X_test,y_test = data.load_video_list(testing_datalist)
X_teidx = np.asarray(np.arange(0, len(y_test)), dtype=np.int32)
y_test  = np.asarray(y_test, dtype=np.int32)
depth_prediction = np.zeros((len(y_test),num_classes), dtype=np.float32)
load_params = tl.files.load_npz(name='%s/fpooling_avg_ft/isogr_depth_birnn_model_epoch_10.npz'%(model_prefix))
tl.files.assign_params(sess, load_params, networks)
#networks.print_params(True)
average_accuracy = 0.0
test_iterations = 0
print '%s: depth testing' % datetime.now()
for X_indices, y_label_t in tl.iterate.minibatches(X_teidx, 
                                                   y_test, 
                                                   batch_size, 
                                                   shuffle=False):
  # Read data for each batch      
  image_path = []
  image_fcnt = []
  image_olen = []
  is_training = []
  for data_a in range(batch_size):
    X_index_a = X_indices[data_a]
    key_str = '%06d' % X_index_a
    image_path.append(X_test[key_str]['videopath'])
    image_fcnt.append(X_test[key_str]['framecnt'])
    image_olen.append(seq_len)
    is_training.append(False) # Testing
    image_info = zip(image_path,image_fcnt,image_olen,is_training)
  X_data_t = tl.prepro.threading_data([_ for _ in image_info], 
                                      data.prepare_isogr_depth_data)
  feed_dict = {x: X_data_t, y: y_label_t}
  dp_dict = tl.utils.dict_to_one(networks.all_drop)
  feed_dict.update(dp_dict)
  predict_value,accu_value,feat_value = sess.run([network_pred, network_accu, feature_stfp], feed_dict=feed_dict)
  depth_prediction[test_iterations*batch_size:(test_iterations+1)*batch_size,:]=predict_value
  testing_feats[test_iterations*batch_size:(test_iterations+1)*batch_size,4096:8192]=feat_value
  average_accuracy = average_accuracy + accu_value
  test_iterations = test_iterations + 1
average_accuracy = average_accuracy / test_iterations
format_str = ('%s: depth average_accuracy = %.6f')
print (format_str % (datetime.now(), average_accuracy))

# Flow
testing_datalist = '/ssd/dataset/IsoGD_Image/valid_flow_list.txt'
X_test,y_test = data.load_video_list(testing_datalist)
X_teidx = np.asarray(np.arange(0, len(y_test)), dtype=np.int32)
y_test  = np.asarray(y_test, dtype=np.int32)
flow_prediction = np.zeros((len(y_test),num_classes), dtype=np.float32)
load_params = tl.files.load_npz(name='%s/fpooling_avg_ft/isogr_flow_birnn_model_epoch_10.npz'%(model_prefix))
tl.files.assign_params(sess, load_params, networks)
#networks.print_params(True)
average_accuracy = 0.0
test_iterations = 0
print '%s: flow testing' % datetime.now()
for X_indices, y_label_t in tl.iterate.minibatches(X_teidx, 
                                                   y_test, 
                                                   batch_size, 
                                                   shuffle=False):
  # Read data for each batch      
  image_path = []
  image_fcnt = []
  image_olen = []
  is_training = []
  for data_a in range(batch_size):
    X_index_a = X_indices[data_a]
    key_str = '%06d' % X_index_a
    image_path.append(X_test[key_str]['videopath'])
    image_fcnt.append(X_test[key_str]['framecnt'])
    image_olen.append(seq_len)
    is_training.append(False) # Testing
    image_info = zip(image_path,image_fcnt,image_olen,is_training)
  X_data_t = tl.prepro.threading_data([_ for _ in image_info], 
                                      data.prepare_isogr_flow_data)
  feed_dict = {x: X_data_t, y: y_label_t}
  dp_dict = tl.utils.dict_to_one(networks.all_drop)
  feed_dict.update(dp_dict)
  predict_value,accu_value,feat_value = sess.run([network_pred, network_accu, feature_stfp], feed_dict=feed_dict)
  flow_prediction[test_iterations*batch_size:(test_iterations+1)*batch_size,:]=predict_value
  testing_feats[test_iterations*batch_size:(test_iterations+1)*batch_size,8192:12288]=feat_value
  average_accuracy = average_accuracy + accu_value
  test_iterations = test_iterations + 1
average_accuracy = average_accuracy / test_iterations
format_str = ('%s: flow average_accuracy = %.6f')
print (format_str % (datetime.now(), average_accuracy))

fusion_prediction = rgb_prediction + depth_prediction + flow_prediction
prediction_values = tf.argmax(fusion_prediction, 1)
final_accuracy = tf.reduce_mean(tf.cast(tf.equal(tf.cast(prediction_values, tf.int32), y_test), tf.float32))
print final_accuracy

np.save("training_feats.npy", training_feats)
np.save("training_label.npy", training_label)
np.save("testing_feats.npy", testing_feats)
np.save("testing_label.npy", testing_label)

video_list = 'valid_list.txt'
f = open(video_list, 'r')
f_lines = f.readlines()
f.close()
f = open('valid_prediction_softmax.txt', 'w')
for idx, line in enumerate(f_lines):
  linetxt = '%s %s %d\n' %(line.split(' ')[0], line.split(' ')[1], prediction_values[idx].eval()+1)
  f.write(linetxt)
f.close()

# In the end, close TensorFlow session.
sess.close()

clf = svm.SVC(decision_function_shape='ovr')
clf.fit(training_feats, training_label)
predict = clf.decision_function(testing_feats).argmax(1)
accuracy = (predict == testing_label).sum() / len(testing_label)

f = open('valid_prediction_svm.txt', 'w')
for idx, line in enumerate(f_lines):
  linetxt = '%s %s %d\n' %(line.split(' ')[0], line.split(' ')[1], predict[idx]+1)
  f.write(linetxt)
f.close()
