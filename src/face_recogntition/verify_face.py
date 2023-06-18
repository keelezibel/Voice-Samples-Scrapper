import os
import typing
from deepface import DeepFace


path_type = typing.Union[str, os.PathLike]


def verify_face(
    img1_path: path_type,
    img2_path: path_type,
    model_name: str,
    distance_metric: str,
    detector_backend: str,
):
    result = DeepFace.verify(
        img1_path=img1_path,
        img2_path=img2_path,
        model_name=model_name,
        distance_metric=distance_metric,
        detector_backend=detector_backend,
    )
    print(result)
    return result


verify_face(
    "ref.jpg",
    "test.jpg",
    model_name="Facenet512",
    distance_metric="euclidean_l2",
    detector_backend="dlib",
)
