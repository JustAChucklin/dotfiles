local M = {}

M.custom = {
  n = {
    ["<leader>gg"] = { "<cmd> :LazyGit <CR>", "LazyGit Plugin" },
    ["<C-w>"] = {"<cmd> :resize -2<CR>", "Resize vertically up" },
    ["<C-s>"] = { "<cmd> :resize +2<CR>", "Resize vertically down" },
    ["<C-D>"] = { "<cmd> :vertical resize -2<CR>", "Resize horizontally right" },
    ["<C-A>"] = { "<cmd> :vertical resize +2<CR>", "Resize horizontally left" },
    ["<leader>o"] = { "<cmd> :RnvimrToggle<CR>", "RangerNvim Toggle" },
    ["<leader>\\"] = { "<cmd> :RnvimrToggle<CR>", "RangerNvim Toggle" },
    ["<leader>ft"] = {
      function()
        require("nvterm.terminal").toggle "float"
      end,
      "New floating term",
    },
    ["<leader>vt"] = {
      function()
        require("nvterm.terminal").toggle "vertical"
      end,
      "New vertical term",
    },
    ["<leader>ht"] = {
      function()
        require("nvterm.terminal").toggle "horizontal"
      end,
      "New horizontal term",
    },
    ["<leader>mp"] = { "<cmd> :MarkdownPreview<CR>", "Open a Markdown Preview" }
  },
}

return M
