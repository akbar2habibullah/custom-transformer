# Internal Latent Loop Transformer
(Multiple internal inference loop transformer model)

![Internal latent loop](https://github.com/user-attachments/assets/f3eec20e-14a6-43dd-b3fd-ee911aac863a)

This is a simple implementation of the iterable Transformer model, where the model can *rethink* its internal cognitive process with an internal confidence score as a guide. Akin of slow thinking mechanism.
So this is the simple explanation of how it works:
- We put an adjustable parameter to handle internal looping, the default value is 1.
- If the loss value is high, this iteration is triggered, with max iterations set to 10.
- We train an independent layer to output a confidence score, trained by loss value from the main training process.
- When inference, both the next token and confidence scores are outputted and can determine how many iterations are needed for the current inference.
- ~~No sophisticated tokenization or attention layer, just a pure simple transformer for learning purpose.~~ I'm adding BPE, RoPE, and safetensors.
