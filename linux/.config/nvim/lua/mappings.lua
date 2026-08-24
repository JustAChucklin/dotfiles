require "nvchad.mappings"

-- add yours here

local map = vim.keymap.set

map("n", ";", ":", { desc = "CMD enter command mode" })
map("i", "jk", "<ESC>")
map("n", "<C-Up>", "<cmd>resize +2<CR>", { desc = "increase window height" })
map("n", "<C-Down>", "<cmd>resize -2<CR>", { desc = "decrease window height" })
map("n", "<C-Left>", "<cmd>vertical resize -2<CR>", { desc = "decrease window width" })
map("n", "<C-Right>", "<cmd>vertical resize +2<CR>", { desc = "increase window width" })
-- map({ "n", "i", "v" }, "<C-s>", "<cmd> w <cr>")
