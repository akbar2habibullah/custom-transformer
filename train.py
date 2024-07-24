import torch
import torch.nn as nn
import torch.optim as optim

from saveModel import save_model_weights, load_model_weights
from main import TransformerModel

from tokenizers import Tokenizer, processors

# Define the constants
VOCAB_SIZE = 32000
EMBED_SIZE = 768
NUM_HEADS = 12
NUM_LAYERS = 6
CONTEXT_SIZE = 512
LEARNING_RATE = 0.001
NUM_EPOCHS = 50
BASE_ITERATIONS = 1
MAX_ITERATIONS = 10
CONFIDENCE_THRESHOLD = 0.8
LOSS_THRESHOLD = 2.0  # Loss value threshold for increasing iterations
IMG_SIZE = 224
PATCH_SIZE = 16
VIT_LAYERS = 3

# Create the model
model = TransformerModel(VOCAB_SIZE, EMBED_SIZE, NUM_HEADS, NUM_LAYERS, CONTEXT_SIZE, IMG_SIZE, PATCH_SIZE, VIT_LAYERS)

# Load tokenizer
tokenizer = Tokenizer.from_file("bpe_tokenizer_autoregressive.json")
tokenizer.post_processor = processors.TemplateProcessing(
    single="[CLS] $A [SEP]",
    pair="[CLS] $A [SEP] $B:1 [SEP]:1",
    special_tokens=[
        ("[CLS]", tokenizer.token_to_id("[CLS]")),
        ("[SEP]", tokenizer.token_to_id("[SEP]")),
    ],
)


# Define the loss function, confidence loss, and optimizer
criterion = nn.CrossEntropyLoss(ignore_index=tokenizer.token_to_id("[PAD]"))
confidence_criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

# Load model weights before training
load_model_weights(model, "model_weights.safetensors")
print("Model weights loaded.")

# Training loop
for epoch in range(NUM_EPOCHS):
    model.train()
    optimizer.zero_grad()

    # Example input (batch size 1, context size 512)
    text = "Your input text here with [IMG][/IMG] and [IMG][/IMG]."
    example_input = torch.tensor(tokenizer.encode(text).ids).unsqueeze(0)[:, :CONTEXT_SIZE]
    target = example_input.clone().detach()
    
    # Example image inputs (batch size 1, 3 channels, 224x224)
    imgs = [torch.randn(1, 3, 224, 224), torch.randn(1, 3, 224, 224)]

    # Shift target for autoregressive training while ignoring image token regions
    target = target[:, 1:].contiguous().view(-1)
    mask = (target != tokenizer.token_to_id("[IMG]")) & (target != tokenizer.token_to_id("[/IMG]"))
    target = target[mask]

    num_iterations = BASE_ITERATIONS
    output, confidence, vit_loss = model(example_input[:, :-1], imgs=imgs, num_iterations=num_iterations, use_cache=True, middle_training=True)
    output = output.view(-1, VOCAB_SIZE)[mask]
    loss = model.criterion(output, target) + vit_loss
    confidence_target = 1 - (loss.item() / LOSS_THRESHOLD)
    confidence_target = torch.tensor([[confidence_target]], dtype=torch.float)
    confidence_loss = confidence_criterion(confidence, confidence_target)

    while confidence.mean().item() < CONFIDENCE_THRESHOLD and num_iterations < MAX_ITERATIONS:
        num_iterations += 1
        output, confidence, vit_loss = model(example_input[:, :-1], imgs=imgs, num_iterations=num_iterations, use_cache=True, middle_training=True)
        output = output.view(-1, VOCAB_SIZE)[mask]
        loss = model.criterion(output, target) + vit_loss
        confidence_target = 1 - (loss.item() / LOSS_THRESHOLD)
        confidence_target = torch.tensor([[confidence_target]], dtype=torch.float)
        confidence_loss = confidence_criterion(confidence, confidence_target)

    total_loss = loss + confidence_loss
    total_loss.backward()
    optimizer.step()

    print(f'Epoch {epoch+1}/{NUM_EPOCHS}, Loss: {loss.item()}, Confidence: {confidence.mean().item()}, Iterations: {num_iterations}')

# Save model weights at the end of training
save_model_weights(model, "model_weights.safetensors")
print("Model weights saved.")

print("Training completed.")
