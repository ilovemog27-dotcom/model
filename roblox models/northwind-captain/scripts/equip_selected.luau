-- Run in the Roblox Studio Command Bar with the accessory and target rig selected.
local Selection = game:GetService("Selection")
local accessory, rig
for _, object in Selection:Get() do
    if object:IsA("Accessory") then accessory = object end
    if object:IsA("Model") and object:FindFirstChildOfClass("Humanoid") then rig = object end
end
assert(accessory, "Select the imported Northwind Captain Accessory in Explorer.")
assert(rig, "Also select an R6 or R15 rig containing a Humanoid.")
local copy = accessory:Clone()
for _, object in copy:GetDescendants() do
    if object:IsA("BasePart") then
        object.Anchored = false
        object.CanCollide = false
        object.CanTouch = false
        object.CanQuery = false
        object.Massless = true
    end
end
rig:FindFirstChildOfClass("Humanoid"):AddAccessory(copy)
Selection:Set({copy})
print("Equipped " .. copy.Name .. " on " .. rig.Name)
