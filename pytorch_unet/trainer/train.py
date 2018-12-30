import argparse
import os
import sys

import numpy as np
import torch
from torch import nn
from torch.optim import Adam

if __name__ == '__main__' and __package__ is None:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    __package__ = "pytorch_unet.trainer"


from pytorch_unet.model.u_net import UNet
from pytorch_unet.processing.load import load_data
from pytorch_unet.utils.helpers import pred_to_numpy, to_numpy
from pytorch_unet.utils.metrics import dice
from pytorch_unet.visualize.logger import Logger
from pytorch_unet.visualize.logger import save_models
from pytorch_unet.visualize.plot import plotter, graph_summary

# CUDA for PyTorch
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# variables
best_loss = 1e10
loss_criterion = nn.BCEWithLogitsLoss()
loss_values = []
threshold_value = 0.5


def parse_args(args):
    parser = argparse.ArgumentParser(description='Script for training the model')

    parser.add_argument('--root_dir', default="C:\\Users\\Mukesh\\Segmentation\\UNet\\", type=str,
                        help='root directory')
    parser.add_argument('--weights_dir', default="./weights", type=str, help='Choose directory to save weights model')
    parser.add_argument('--log_dir', default="./train_logs", type=str, help='Choose directory to save the logs')
    parser.add_argument('--image_size', default=64, type=int, help='resize image size')
    parser.add_argument('--batch_size', default=4, type=int, help='batch size')
    parser.add_argument('--epochs', default=2, type=int)
    parser.add_argument('--depth', default=3, type=int, help='Number of downsampling/upsampling blocks')
    parser.add_argument('--n_classes', default=1, type=int, help='Number of classes in the dataset')
    parser.add_argument('--up_mode', default='upsample', choices=['upconv, upsample'], type=str,
                        help='Type of upsampling')
    parser.add_argument('--augment', default='yes', choices=['yes, no'], type=str,
                        help='Whether to augment the train images or not')
    parser.add_argument('--augment_type', default='geometric', choices=['geometric, image, both'], type=str,
                        help='Which type of augmentation to choose from: geometric, brightness or both')
    parser.add_argument('--transform_prob', default=0.5, type=int,
                        help='Probability of images to augment when calling augmentations')
    parser.add_argument('--test_size', default=0.2, type=int,
                        help='Validation size to split the data, should be in between 0.0 to 1.0')
    parser.add_argument('--log', default='no', choices=['yes', 'no'], type=str, help='Log the Values')
    parser.add_argument('--build_graph', default='no', choices=['yes', 'no'], type=str, help='Build the model graph')

    return parser.parse_args(args)


def validate_model(model, loader, threshold):
    """ Contains the validation loop"""
    model = model.eval()
    for i, data in enumerate(loader):
        val_batch, val_labels = data
        val_batch, val_labels = val_batch.to(device), val_labels.to(device)

        # call the u-net module
        prediction = model(val_batch)

        # call the loss function
    loss = loss_criterion(prediction, val_labels)
    pred_labels, true_labels = pred_to_numpy(prediction) > threshold, to_numpy(val_labels) > threshold
    dices = []
    for _pred, _labels in zip(pred_labels, true_labels):
        dices.append(dice(_pred, _labels))

    return np.array(dices).mean(), loss.detach().cpu().numpy()


def training_loop(train_loader, model, optim, val_loader, args):
    """Contains the training loop"""
    global best_loss

    for e in range(args.epochs):
        for i, data in enumerate(train_loader):
            train_batch, train_labels = data
            train_batch, train_labels = train_batch.to(device), train_labels.to(device)

            # call the u-net module
            prediction = model(train_batch)

            # call the loss function
            loss = loss_criterion(prediction, train_labels)
            loss_values.append(loss)

            # backward pass
            optim.zero_grad()
            loss.backward()
            optim.step()

        with torch.no_grad():
            train_dice, train_loss = validate_model(model, train_loader, threshold=threshold_value)
            val_dice, val_loss = validate_model(model, val_loader, threshold=threshold_value)
            # print the loss
            print("===> Epoch {} Training Loss: {:.4f} : Mean Dice: {:.4f}".format(e, train_loss, train_dice))
            print("===> Epoch {} Validation Loss: {:.4f} : Mean Dice: {:.4f} :".format(e, val_loss, val_dice))

        # log train history
        if args.log == 'yes':
            logger = Logger(args.log_dir)
            plotter(log=logger, train_loss=train_loss, train_dice=train_dice, val_loss=val_loss, val_dice=val_dice,
                    step=e, model=model)

        # save model with best score
        is_best = val_loss < best_loss
        best_loss = min(val_loss, best_loss)
        save_models(model=model, path=args.weights_dir, epoch=e + 1, optimizer=optim, best=is_best, loss=best_loss)

    return prediction


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    args = parse_args(args)

    if not os.path.exists(args.weights_dir):
        os.makedirs(args.weights_dir)

    if not os.path.exists(args.log_dir):
        os.makedirs(args.log_dir)

    train_loader, val_loader = load_data(args)

    # create the model
    model = UNet(in_channels=1, n_classes=args.n_classes, depth=args.depth, wf=6, padding=True, batch_norm=False,
                 up_mode=args.up_mode).to(device)

    # create the optimizer
    optim = Adam(model.parameters())

    # start the training loop
    prediction = training_loop(train_loader, model, optim, val_loader, args)
    print("Training Done!")

    if args.log == 'yes':
        print("\nTo view the logs run tensorboard in your command line from the trainer folder"
              ": tensorboard --logdir=train_logs/ --port=6006"
              "\nYou can view the results at:  http://localhost:6006")

    if args.build_graph == 'yes':
        graph = graph_summary(prediction.mean(), params=dict(model.named_parameters()))
        graph.format = 'png'
        graph.render('u_net_model')
        print("Model Graph Built")


if __name__ == '__main__':
    main()