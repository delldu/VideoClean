"""Data loader."""
# coding=utf-8
#
# /************************************************************************************
# ***
# ***    Copyright Dell 2020, All Rights Reserved.
# ***
# ***    File Author: Dell, 2020年 11月 02日 星期一 17:51:08 CST
# ***
# ************************************************************************************/
#

import os
import pdb

import torch
import torch.utils.data as data
import torchvision.transforms as T
import torchvision.utils as utils
from PIL import Image

train_dataset_rootdir = "dataset/train/"
test_dataset_rootdir = "dataset/test/"
VIDEO_SEQUENCE_LENGTH = 5


def get_transform(train=True):
    """Transform images."""
    ts = []
    # if train:
    #     ts.append(T.RandomHorizontalFlip(0.5))

    ts.append(T.ToTensor())
    return T.Compose(ts)


class Video(data.Dataset):
    """Define Video Frames Class."""

    def __init__(self, seqlen=VIDEO_SEQUENCE_LENGTH, transforms=get_transform()):
        """Init dataset."""
        super(Video, self).__init__()
        self.seqlen = seqlen
        self.transforms = transforms
        self.root = ""
        self.images = []

    def reset(self, root):
        # print("Video Reset Root: ", root)
        self.root = root
        self.images = list(sorted(os.listdir(root)))

    def __getitem__(self, idx):
        """Load images."""
        n = len(self.images)
        filelist = []
        for k in range(-(self.seqlen//2), (self.seqlen//2) + 1):
            if (idx + k < 0):
                filename = self.images[0]
            elif (idx + k >= n):
                filename = self.images[n - 1]
            else:
                filename = self.images[idx + k]
            filelist.append(os.path.join(self.root, filename))
        # print("filelist: ", filelist)
        sequence = []
        for filename in filelist:
            img = Image.open(filename).convert("RGB")
            if self.transforms is not None:
                img = self.transforms(img)
            sequence.append(img)
        if self.transforms is not None:
            return torch.cat(sequence, dim=0)
        return sequence

    def __len__(self):
        """Return total numbers of images."""
        return len(self.images)


class VideoCleanDataset(data.Dataset):
    """Define dataset."""

    def __init__(self, root, seqlen, transforms=get_transform()):
        """Init dataset."""
        super(VideoCleanDataset, self).__init__()

        self.root = root
        self.seqlen = seqlen
        self.transforms = transforms

        # load all images, sorting for alignment
        self.images = []
        # index start offset
        self.indexs = []
        offset = 0
        ds = list(sorted(os.listdir(root)))
        for d in ds:
            fs = sorted(os.listdir(root + "/" + d))
            for f in fs:
                self.images.append(d + "/" + f)
                self.indexs.append(offset)
            offset += len(fs)
        self.video_cache = Video(seqlen=seqlen, transforms=transforms)

    def __getitem__(self, idx):
        """Load images."""
        # print("dataset index:", idx)
        image_path = os.path.join(self.root, self.images[idx])
        if (self.video_cache.root != os.path.dirname(image_path)):
            self.video_cache.reset(os.path.dirname(image_path))
        return self.video_cache[idx - self.indexs[idx]]

    def __len__(self):
        """Return total numbers of images."""
        return len(self.images)

    def __repr__(self):
        """
        Return printable representation of the dataset object.
        """
        fmt_str = 'Dataset ' + self.__class__.__name__ + '\n'
        fmt_str += '    Number of samples: {}\n'.format(self.__len__())
        fmt_str += '    Root Location: {}\n'.format(self.root)
        tmp = '    Transforms: '
        fmt_str += '{0}{1}\n'.format(
            tmp, self.transforms.__repr__().replace('\n', '\n' + ' ' * len(tmp)))
        return fmt_str


def train_data(bs):
    """Get data loader for trainning & validating, bs means batch_size."""

    train_ds = VideoCleanDataset(
        train_dataset_rootdir, VIDEO_SEQUENCE_LENGTH, get_transform(train=True))
    print(train_ds)

    # Split train_ds in train and valid set
    valid_len = int(0.2 * len(train_ds))
    indices = [i for i in range(len(train_ds) - valid_len, len(train_ds))]

    valid_ds = data.Subset(train_ds, indices)
    # adjust index offset of valid_ds
    # offset = valid_ds.indexs[0]
    # for i in range(len(valid_ds)):
    #     valid_ds.indexs[i] -= offset

    indices = [i for i in range(len(train_ds) - valid_len)]
    train_ds = data.Subset(train_ds, indices)

    # Define training and validation data loaders
    n_threads = min(4,  bs)
    train_dl = data.DataLoader(
        train_ds, batch_size=bs, shuffle=True, num_workers=n_threads)
    valid_dl = data.DataLoader(
        valid_ds, batch_size=bs, shuffle=False, num_workers=n_threads)

    return train_dl, valid_dl


def test_data(bs):
    """Get data loader for test, bs means batch_size."""

    test_ds = VideoCleanDataset(
        test_dataset_rootdir, VIDEO_SEQUENCE_LENGTH, get_transform(train=False))
    test_dl = data.DataLoader(test_ds, batch_size=bs,
                              shuffle=False, num_workers=4)

    return test_dl


def get_data(trainning=True, bs=4):
    """Get data loader for trainning & validating, bs means batch_size."""

    return train_data(bs) if trainning else test_data(bs)


def VideoCleanDatasetTest():
    """Test dataset ..."""

    ds = VideoCleanDataset(train_dataset_rootdir, seqlen=VIDEO_SEQUENCE_LENGTH)
    print(ds)
    print(ds[10].size())

    # vs = Video()
    # vs.reset("dataset/predict/input")


if __name__ == '__main__':
    VideoCleanDatasetTest()
