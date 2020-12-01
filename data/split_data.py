import os
import random
imgs = os.listdir('work/metric_learning/data/Market-1501/gt_bbox')
imgs.sort()
image_id = 1
super_class_id = 1
class_id = 1
class_dict = {}
for img in imgs:
    if 'jpg' in img:
        person_id = img[:4]
        if person_id not in class_dict:
            class_dict[person_id] = class_id
            class_id += 1

total = []
for img in imgs:
    if 'jpg' in img:
        person_id = img[:4]
        path = 'gt_bbox/'+img
        line = '%s %s %s %s\n' % (image_id, class_dict[person_id], super_class_id, path)
        image_id += 1
        total.append(line)

# random.shuffle(total)
train = total[:-1014]
dev = total[-1014:]


with open('work/metric_learning/data/Market-1501/train.txt', 'w', encoding='UTF-8') as f:
    f.write('image_id class_id super_class_id path\n')
    for line in train:
        f.write(line)
    
with open('work/metric_learning/data/Market-1501/test.txt', 'w', encoding='UTF-8') as f:
    f.write('image_id class_id super_class_id path\n')
    for line in dev:
        f.write(line)