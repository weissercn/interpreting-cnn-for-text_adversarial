import json
from data import load_data, get_epoch
import torch
import math
from torch import nn
import os
import numpy as np
import argparse


def eval_adversary(model, data, config):

    model.eval()
    n_iter = 0
    #epoch_x, epoch_y, lengths_x = get_epoch(data["valid_x"], data["valid_y"], config["batch_size"], is_train=False)
    epoch_x, epoch_y, lengths_x = get_epoch(data["valid_x"], data["valid_y"], 1, is_train=False) #num_examples=1)
    epoch_loss = 0
    corrects = 0
    criterion = nn.CrossEntropyLoss()

    advers_attack = {
        "TP": [],
        "TN": [data["word_to_idx"][a] for a in ["surreal", "heart"]],
        "FP": [],
        "FN": [data["word_to_idx"][a] for a in ["surreal", "heart"]],
        }


    results = {    
        "TP": [0,0], # number of examples changed and unchanged by adversarial attack
        "TN": [0,0],
        "FP": [0,0],
        "FN": [0,0], 
        }

    for batch_x, batch_y, length_x in zip(epoch_x, epoch_y, lengths_x):
        #batch_x_advers = [a+advers_attack for a in batch_x ]
        #length_x_advers = [a+len(advers_attack) for a in  length_x]
        
        batch_x_orig = batch_x.copy()
        length_x_orig = length_x.copy()
        #batch_x_advers_orig = batch_x_advers.copy()

        batch_x = torch.LongTensor(batch_x)
        batch_y = torch.LongTensor(batch_y)
        lengths_x = torch.LongTensor(length_x)

        if config["cuda"]:
            batch_x, batch_y, lengths_x = batch_x.cuda(), batch_y.cuda(), lengths_x.cuda()

        # optimizer.zero_grad()
        pred = model(batch_x)['logits']
        pred_class = torch.max(pred, 1)[1].view(batch_y.size()).data
        batch_y_orig = batch_y.clone()
        if config["cuda"]:
            pred_class = pred_class.cpu().detach().numpy()
            batch_y = batch_y.cpu().detach().numpy()

        #this only works if batch size is 1

        TYPE = ""
        if pred_class[0]==1 and batch_y[0]==1: TYPE = "TP"
        elif pred_class[0]==0 and batch_y[0]==0: TYPE = "TN"
        elif pred_class[0]==0 and batch_y[0]==1: TYPE = "FP"
        elif pred_class[0]==1 and batch_y[0]==0: TYPE = "FN"

        if TYPE=="TN": # Adversarial attack on negative samples. If the model correctly predicts that a sample belongs to class 0. 
            # TN 
            batch_x_advers_orig = [a+advers_attack[TYPE] for a in batch_x_orig ]
            length_x_advers_orig = [a+len(advers_attack[TYPE]) for a in  length_x_orig]
            
            batch_x_advers = torch.LongTensor(batch_x_advers_orig)
            lengths_x_advers = torch.LongTensor(length_x_advers_orig)

            if config["cuda"]:
                batch_x_advers, lengths_x_advers = batch_x_advers.cuda(), lengths_x_advers.cuda()

            # optimizer.zero_grad()
            pred_advers = model(batch_x_advers)['logits']
            pred_class_advers = torch.max(pred_advers, 1)[1].view(batch_y_orig.size()).data
            if config["cuda"]:
                pred_class_advers = pred_class_advers.cpu().detach().numpy()

            if pred_class[0] == pred_class_advers[0]: results[TYPE][1]+=1
            else: results[TYPE][0]+=1

            if False:
                #print(data["idx_to_word"].keys(), len(data["idx_to_word"].keys()))
                print("Original sentence : ", " ".join([data["idx_to_word"][a] for a in batch_x_orig[0]  ]))
                print("Adversarial sentence : ", " ".join([data["idx_to_word"][a] for a in batch_x_advers_orig[0]  ]))
                print("Truth {}, Pred {}, Adversarial {}".format(batch_y[0],pred_class[0],pred_class_advers[0] ))


    print("results : ", results)        





if __name__ == '__main__': #original
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config", type=str, required=True)

    args = parser.parse_args()

    with open(args.config) as fp:
        adversarial_config = json.load(fp)

    model_path = adversarial_config["model_path"]
    with open(model_path+'/config.json') as fp:
        config = json.load(fp)

    config.update(adversarial_config)

    with open(model_path+'/w2i.json') as fp:
        w2i = json.load(fp)

    data = load_data(config=config, word_to_idx=w2i)

    model = torch.load(model_path+'/model')

    if config["cuda"]:
        model = model.cuda()


    eval_adversary(model=model, data=data, config=config)


