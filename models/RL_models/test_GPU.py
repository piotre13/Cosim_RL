import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("CUDA available: ", torch.cuda.is_available())
print(f"Using device: {device}")
print(torch.cuda.device_count())
