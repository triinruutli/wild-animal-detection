
Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/11MTKGR2S08jp4R0KxKSCZ3DmBTACuNce

# Install libraries
"""

!pip install pyyaml==5.1

import torch
!pip install 'git+https://github.com/facebookresearch/detectron2.git'

# Setup detectron2 logger
import detectron2
from detectron2.utils.logger import setup_logger 

# import some common libraries
import numpy as np
import os, json, cv2, random
from google.colab.patches import cv2_imshow

# import some common detectron2 utilities
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog, DatasetCatalog

"""# Prepare animal dataset"""

from google.colab import drive
drive.mount('/content/drive')

os.chdir('/content/drive/MyDrive/ColabNotebooks/AnimalDetection/Data/train_multiple')
for  f in enumerate(os.listdir()):
  f_name = f[1].split(".")
  new_name = f_name[0]+".jpg"
  os.rename(f[1], new_name)

#use this code for instance segmentation when labels=6
from detectron2.data.datasets import register_coco_instances
register_coco_instances("animals_train", {}, "/content/drive/MyDrive/ColabNotebooks/AnimalDetection/Data/annotations/annotations_test_0705.json", "/content/drive/MyDrive/ColabNotebooks/AnimalDetection/Data/train_multiple")
register_coco_instances("animals_val", {}, "/content/drive/MyDrive/ColabNotebooks/AnimalDetection/Data/annotations/annotations_val_0705.json", "/content/drive/MyDrive/ColabNotebooks/AnimalDetection/Data/val_multiple")

dataset_dicts = DatasetCatalog.get("animals_train")
for d in random.sample(dataset_dicts, 1):
    img = cv2.imread(d["file_name"])
    visualizer = Visualizer(img[:, :, ::-1], metadata=MetadataCatalog.get("animals_train"), scale=1)
    out = visualizer.draw_dataset_dict(d)
    pic=out.get_image()[:, :, ::-1]
    cv2_imshow(pic)

"""# Train Fast R-CNN

"""
from detectron2.engine import DefaultTrainer

cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml"))
cfg.DATASETS.TRAIN = ("animals_train",)
cfg.DATASETS.TEST = ()
cfg.INPUT.MASK_FORMAT="polygon"
cfg.DATALOADER.NUM_WORKERS = 4
cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml")
cfg.SOLVER.IMS_PER_BATCH = 2
cfg.SOLVER.BASE_LR = 0.002  # pick a good LR
cfg.SOLVER.MAX_ITER = 500    # 200 iterations seems good enough for this toy dataset
cfg.SOLVER.STEPS = []        
cfg.MODEL.ROI_HEADS.NUM_CLASSES = 6

os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
trainer = DefaultTrainer(cfg) 
trainer.resume_or_load(resume=False)
trainer.train()

weights=os.path.join(cfg.OUTPUT_DIR, "model_final.pth")
cfg.MODEL.WEIGHTS = os.path.join(cfg.OUTPUT_DIR, "model_final.pth")  # path to the model we just trained
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.7   # set a custom testing threshold
predictor = DefaultPredictor(cfg)

# Look at training curves in tensorboard:
# %load_ext tensorboard
# %tensorboard --logdir output

from detectron2.utils.visualizer import ColorMode
dataset_dicts = DatasetCatalog.get("animals_val")
for d in random.sample(dataset_dicts, 2):    
    im = cv2.imread(d["file_name"])
    outputs = predictor(im)  # format is documented at https://detectron2.readthedocs.io/tutorials/models.html#model-output-format
    v = Visualizer(im[:, :, ::-1],
                   metadata=MetadataCatalog.get("animals_val"), 
                   scale=1, 
                   instance_mode=ColorMode.IMAGE_BW   # remove the colors of unsegmented pixels. This option is only available for segmentation models
    )
    out = v.draw_instance_predictions(outputs["instances"].to("cpu"))
    image= out.get_image()[:, :, ::-1]
    cv2_imshow(image)

cv2.imwrite("output.jpg",image)

from detectron2.evaluation import COCOEvaluator, inference_on_dataset
from detectron2.data import build_detection_test_loader
evaluator = COCOEvaluator("animals_val", output_dir="./output")
val_loader = build_detection_test_loader(cfg, "animals_val")
print(inference_on_dataset(predictor.model, val_loader, evaluator))
# another equivalent way to evaluate the model is to use `trainer.test`

"""# Video output"""

# Commented out IPython magic to ensure Python compatibility.
from detectron2.data import datasets
!git clone https://github.com/facebookresearch/detectron2

# %run detectron2/demo/demo.py --config-file /content/drive/MyDrive/ColabNotebooks/config_instance.yaml --video-input /content/drive/MyDrive/ColabNotebooks/AnimalDetection/Data/rabbit2.avi --confidence-threshold 0.7 --output video-output-drabbit2.mkv \
  --opts MODEL.WEIGHTS /content/output/model_final.pth



from google.colab import files
files.download('video-output-drabbit2.mkv')
