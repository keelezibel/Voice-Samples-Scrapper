import os
import csv
import numpy as np
import tensorflow as tf
import tensorboard as tb

from glob import glob
from torchvision import transforms
from PIL import Image
from tqdm import tqdm

import torch
import torchaudio
from speechbrain.pretrained import EncoderClassifier
from torch.utils.tensorboard import SummaryWriter

RUN_NAME = "/app/src/visualization/runs/spkr_ident_full"
# RUN_NAME = "/app/src/visualization/runs/spkr_ident_nameonly"
# RUN_NAME = "/app/src/visualization/runs/spkr_ident_ref"

writer = SummaryWriter(RUN_NAME)
tf.io.gfile = tb.compat.tensorflow_stub.io.gfile


def get_embeddings(filepath):
    classifier = EncoderClassifier.from_hparams(
        source="/app/models/sb_ecapa_pretrained",
        savedir="/app/models/sb_ecapa_pretrained",
    )
    signal, _ = torchaudio.load(filepath)
    embeddings = classifier.encode_batch(signal)
    embeddings = torch.flatten(embeddings)
    return embeddings


def iterate_all_files(dir):
    embeddings = []
    spkrs = []
    audio_files = glob(dir)
    for file in tqdm(audio_files):
        file_dir = os.path.dirname(file)
        filename = os.path.basename(file).split(".wav")[0]
        spkr_name = file_dir.split(os.path.sep)[-1]  # Spkr Name (str)
        embedding = get_embeddings(file)  # Tensors

        embeddings.append(embedding)
        spkrs.append(f"{spkr_name}_{filename}")
        # spkrs.append(spkr_name)
    return spkrs, embeddings


if __name__ == "__main__":
    audio_files_dir = r"/app/data/processed_audio/**/*.wav"
    # audio_files_dir = r"/app/data/ref_audio/**/*.wav"
    spkrs, embeddings = iterate_all_files(audio_files_dir)

    embeddings_reshape = torch.stack(embeddings, 0)
    print(embeddings_reshape.shape)
    print(len(spkrs))

    writer.add_embedding(embeddings_reshape, spkrs)
    writer.close()
