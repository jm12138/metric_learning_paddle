# metric_learning_paddle
## 简介
* 一个简单的行人重识别(RE-ID)模型
* 本项目基于Paddle官方模型库中的[Metric Learning](https://github.com/PaddlePaddle/models/tree/develop/PaddleCV/metric_learning)模型开发
* 清理代码，并修复了几个小Bug
* 增加了几个BackBone：GhostNet、MobileNetV3、ResNetVd
* 增加模型导出脚本，导出模型可用于[deep_sort_paddle](https://github.com/jm12138/deep_sort_paddle)项目中

## 快速使用
* 克隆项目代码：
```
$ git clone https://github.com/jm12138/metric_learning_paddle

$ cd metric_learning_paddle
```
* 下载数据集：[Market-1501](http://bj.bcebos.com/v1/ai-studio-online/8175a303e0634486b9a6341c030947428aeeeb2fda294630bc64779a3d9ec135?responseContentDisposition=attachment%3B%20filename%3DMarket-1501-v15.09.15.tar&authorization=bce-auth-v1%2F0ef6765c1e494918bc0d4c3ca3e5c6d1%2F2018-11-05T12%3A10%3A54Z%2F-1%2F%2F313da33f628e3e9bad2c78bf7417843637d393eb054608afe06780065ca95a36)

* 解压数据集至./data

* 分割数据集：
```
$ python data/split_data.py
```
* 下载预训练模型：
```
$ mkdir pretrained_model

$ wget https://paddle-imagenet-models-name.bj.bcebos.com/ResNet50_vd_ssld_v2_pretrained.tar -P pretrained_model

$ tar -xf pretrained_model/ResNet50_vd_ssld_v2_pretrained.tar -C pretrained_model
```
* 模型训练
```shell
$ python train_elem.py \
    --model ResNet50_vd \
    --embedding_size 128 \
    --train_batch_size 256 \
    --test_batch_size 256 \
    --image_shape 3,128,128 \
    --class_dim 1421 \
    --lr 0.1 \
    --lr_strategy piecewise_decay \
    --lr_steps 5000,7000,9000 \
    --total_iter_num 10000 \
    --display_iter_step 10 \
    --test_iter_step 500 \
    --save_iter_step 500 \
    --use_gpu True \
    --pretrained_model pretrained_model/ResNet50_vd_ssld_v2_pretrained \
    --model_save_dir save_elem_model \
    --loss_name arcmargin \
    --arc_scale 80.0 \
    --arc_margin 0.15 \
    --arc_easy_margin False
```
* 模型微调
```shell
$ python train_pair.py \
    --model ResNet50_vd \
    --embedding_size 128 \
    --train_batch_size 64 \
    --test_batch_size 64 \
    --image_shape 3,128,128 \
    --class_dim 1421 \
    --lr 0.0001 \
    --lr_strategy piecewise_decay \
    --lr_steps 3000,6000,9000 \
    --total_iter_num 10000 \
    --display_iter_step 10 \
    --test_iter_step 500 \
    --save_iter_step 500 \
    --use_gpu True \
    --pretrained_model save_elem_model/ResNet50_vd/10000 \
    --model_save_dir save_pair_model \
    --loss_name eml \
    --samples_each_class 4 \
    --margin 0.1 \
    --npairs_reg_lambda 0.01
```
* 模型评估
```shell
$ python eval.py \
    --model ResNet50_vd \
    --embedding_size 128 \
    --batch_size 256 \
    --image_shape 3,128,128 \
    --use_gpu True \
    --pretrained_model [path to your model]
```
* 模型预测
```shell
$ python infer.py \
    --model ResNet50_vd \
    --embedding_size 128 \
    --batch_size 1 \
    --image_shape 3,128,128 \
    --use_gpu True \
    --pretrained_model [path to your model]
```
* 模型导出
```shell
$ python export_model.py \
    --model ResNet50_vd \
    --embedding_size 128 \
    --image_shape 3,128,128 \
    --use_gpu True \
    --pretrained_model=[path to your model] \
    --model_save_dir=save_inference_model
```

