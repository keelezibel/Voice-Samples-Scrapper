##############################################################################################
"""
This script will ...
"""
##############################################################################################

import numpy as np
from speechbrain.pretrained import SpeakerRecognition

verification = SpeakerRecognition.from_hparams(
    source="/app/models/sb_ecapa_pretrained",
    savedir="pretrained_models/spkrec-ecapa-voxceleb",
)

# Same speaker
score, prediction = verification.verify_files(
    "/app/data/processed_audio/YB DATO SRI MUSTAPA BIN MOHAMED/N5EuFsy81bs_10.wav",
    "/app/data/ref_audio/YB DATO SRI MUSTAPA BIN MOHAMED/26QGffW4r9o.wav",
)
print(score, prediction)
