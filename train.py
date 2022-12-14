import os
import sys
import time
import glob
import numpy as np
import torch
import utils
from PIL import Image
import logging
import argparse
import torch.utils
import torch.backends.cudnn as cudnn
import torch.nn as nn
from torch.autograd import Variable
from tqdm import tqdm

from model import *
from multi_read_data import MemoryFriendlyLoader


device_ids = [0, 1, 2, 3]


parser = argparse.ArgumentParser("SCI")
parser.add_argument('--batch_size', type=int, default=2, help='batch size')
parser.add_argument('--cuda', default=True, type=bool, help='Use CUDA to train model')
parser.add_argument('--gpu', type=str, default='0', help='gpu device id')
parser.add_argument('--seed', type=int, default=2, help='random seed')
parser.add_argument('--epochs', type=int, default=30, help='epochs')
parser.add_argument('--lr', type=float, default=0.0003, help='learning rate')
parser.add_argument('--stage', type=int, default=3, help='epochs')
parser.add_argument('--save', type=str, default='EXP/', help='location of the data corpus')

args = parser.parse_args()

os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu

args.save = args.save + '/' + 'Train-{}'.format(time.strftime("%Y%m%d-%H%M%S"))
utils.create_exp_dir(args.save, scripts_to_save=glob.glob('*.py'))
model_path = args.save + '/model_epochs/'
os.makedirs(model_path, exist_ok=True)
image_path = args.save + '/image_epochs/'
os.makedirs(image_path, exist_ok=True)

log_format = '%(asctime)s %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format=log_format, datefmt='%m/%d %I:%M:%S %p')
fh = logging.FileHandler(os.path.join(args.save, 'log.txt'))
fh.setFormatter(logging.Formatter(log_format))
logging.getLogger().addHandler(fh)

logging.info("train file name = %s", os.path.split(__file__))

if torch.cuda.is_available():
    if args.cuda:
        torch.set_default_tensor_type('torch.cuda.FloatTensor')
    if not args.cuda:
        print("WARNING: It looks like you have a CUDA device, but aren't " +
              "using CUDA.\nRun with --cuda for optimal training speed.")
        torch.set_default_tensor_type('torch.FloatTensor')
else:
    torch.set_default_tensor_type('torch.FloatTensor')


def save_images(tensor, path):
    image_numpy = tensor[0].cpu().float().numpy()
    image_numpy = (np.transpose(image_numpy, (1, 2, 0)))
    im = Image.fromarray(np.clip(image_numpy * 255.0, 0, 255.0).astype('uint8'))
    im.save(path, 'png')


def main():
    if not torch.cuda.is_available():
        logging.info('no gpu device available')
        sys.exit(1)

    np.random.seed(args.seed)
    cudnn.benchmark = True
    torch.manual_seed(args.seed)
    cudnn.enabled = True
    torch.cuda.manual_seed(args.seed)
    logging.info('gpu device = %s' % args.gpu)
    logging.info("args = %s", args)


    model = Network(stage=args.stage)
    
    model.enhance.in_conv.apply(model.weights_init)
    model.enhance.conv.apply(model.weights_init)
    model.enhance.out_conv.apply(model.weights_init)
    model.calibrate.in_conv.apply(model.weights_init)
    model.calibrate.convs.apply(model.weights_init)
    model.calibrate.out_conv.apply(model.weights_init)

    model = model.cuda()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, betas=(0.9, 0.999), weight_decay=3e-4)
    MB = utils.count_parameters_in_MB(model)
    logging.info("model size = %f", MB)
    print(MB)


    train_low_data_names = './dataset/RAWTEST'
    TrainDataset = MemoryFriendlyLoader(img_dir=train_low_data_names, task='train')


    test_low_data_names = './dataset/RAWTEST'
    TestDataset = MemoryFriendlyLoader(img_dir=test_low_data_names, task='test')

    train_queue = torch.utils.data.DataLoader(
        TrainDataset, batch_size=args.batch_size,
        pin_memory=True, num_workers=0, shuffle=True, generator=torch.Generator(device='cuda'))

    test_queue = torch.utils.data.DataLoader(
        TestDataset, batch_size=1,
        pin_memory=True, num_workers=0, shuffle=True, generator=torch.Generator(device='cuda'))

    total_step = 0

    for epoch in range(args.epochs):
        model.train()
        losses = []
        loop = tqdm(enumerate(train_queue), total =len(train_queue))
        for batch_idx, (input, _) in loop:
            total_step += 1
            input = Variable(input, requires_grad=False).cuda()

            optimizer.zero_grad()
            loss = model._loss(input)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 5)
            optimizer.step()

            losses.append(loss.item())

            loop.set_description(f'Epoch [{epoch}/{args.epochs}] Train')
            loop.set_postfix(loss = np.average(losses))

            # logging.info('train-epoch %03d %03d %f', epoch, batch_idx, loss)

        # logging.info('Train average loss %f',np.average(losses))
        utils.save(model, os.path.join(model_path, 'weights_%d.pt' % epoch))

        if epoch % 1 == 0 and total_step != 0:
            # logging.info('train %03d %f', epoch, loss)
            model.eval()
            with torch.no_grad():
                loop = tqdm(enumerate(test_queue), total =len(test_queue))
                for _, (input, image_name) in loop:
                    input = Variable(input).cuda()
                    image_name = image_name[0].split('/')[-1].split('.')[0]
                    illu_list, ref_list, input_list, atten= model(input)
                    u_name = '%s.png' % (image_name + '_' + str(epoch))
                    u_path = image_path + '/' + u_name
                    save_images(ref_list[0], u_path)

                    loop.set_description(f'Epoch [{epoch}/{args.epochs}] Test ')

if __name__ == '__main__':
    main()