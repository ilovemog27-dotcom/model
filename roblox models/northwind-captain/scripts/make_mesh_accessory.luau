-- Optional: run after importing the FBX/OBJ as ONE MeshPart.
-- Select the imported MeshPart (or its one-mesh wrapper Model) in Explorer.
local Selection = game:GetService("Selection")
local candidates = {}
for _, selected in Selection:Get() do
    if selected:IsA("MeshPart") then
        table.insert(candidates, selected)
    elseif selected:IsA("Model") then
        for _, object in selected:GetDescendants() do
            if object:IsA("MeshPart") then table.insert(candidates, object) end
        end
    end
end
assert(#candidates == 1, "Select exactly one imported Northwind Captain MeshPart.")
local handle = candidates[1]
local accessory = Instance.new("Accessory")
accessory.Name = "Northwind Captain"
accessory.AccessoryType = Enum.AccessoryType.Hat
handle.Name = "Handle"
handle.Anchored = false
handle.CanCollide = false
handle.CanTouch = false
handle.CanQuery = false
handle.Massless = true
handle.Color = Color3.new(1, 1, 1)
handle.Material = Enum.Material.SmoothPlastic
handle.Size = Vector3.new(2.32362097, 1.13109821, 2.43750047)
handle.CFrame = CFrame.new(0, 0.0950326174, -0.239072964)
handle.PivotOffset = CFrame.identity
handle.Parent = accessory
local old = handle:FindFirstChild("HatAttachment")
if old then old:Destroy() end
local attachment = Instance.new("Attachment")
attachment.Name = "HatAttachment"
attachment.CFrame = CFrame.new(0, -0.495032617, 0.239072964)
attachment.Parent = handle
accessory.Parent = workspace
Selection:Set({accessory})
print("Created Northwind Captain accessory; use equip_selected.luau with a selected rig.")
