-- rbxmk v0.9.1: input.rbxmx, then output.rbxm.
local input, output = ...
assert(input and output, "Pass input.rbxmx and output.rbxm")
fs.write(output, fs.read(input))
