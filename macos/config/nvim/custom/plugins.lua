local plugins = {
  -- {
  --   'glepnir/dashboard-nvim',
  --   lazy = false,
  --   event = 'VimEnter',
  --   config = function()
  --     require('dashboard').setup {
  --       theme = 'doom', 
  --       header  = require "custom.functions".randomsplash(),
  --       center = {
  --         { "  Find File", "Spc f f", "Telescope find_files" },
  --         { "󰈚  Recent Files", "Spc f o", "Telescope oldfiles" },
  --         { "󰈭  Find Word", "Spc f w", "Telescope live_grep" },
  --         { "  Bookmarks", "Spc m a", "Telescope marks" },
  --         { "  Themes", "Spc t h", "Telescope themes" },
  --         { "  Mappings", "Spc c h", "NvCheatsheet" }  --         {
  --       },
  --     }
  --   end,
  --   dependencies = { {'nvim-tree/nvim-web-devicons'}}
  -- }, 
  {
    "kevinhwang91/rnvimr",
    cmd = "RnvimrToggle",
    lazy = false,
    config = function()
      vim.g.rnvimr_draw_border = 1
      vim.g.rnvimr_pick_enable = 1
      vim.g.rnvimr_bw_enable = 1
    end,
  },
  {
    "ggandor/leap.nvim",
    name = "leap",
    lazy = false,
    config = function()
      require("leap").add_default_mappings()
    end,
  },
  {
    "Mofiqul/dracula.nvim",
     config = function()
      require("dracula").setup({
        colors = {
          bg = "#22212c",
          fg = "#F8F8F2",
          selection = "#454158",
          comment = "#7970a9",
          red = "#ff9580",
          orange = "#ffca80",
          yellow = "#ffff80",
          green = "#8aff80",
          purple = "#9580ff",
          cyan = "#80ffea",
          pink = "#ff80bf",
          bright_red = "#ffaa99",
          bright_green = "#a2ff99",
          bright_yellow = "#ffff99",
          bright_blue = "#aa99ff",
          bright_magenta = "#ff99cc",
          bright_cyan = "#99ffee",
          bright_white = "#FFFFFF",
          menu = "#0b0b0f",
          visual = "#2e2b3b",
          gutter_fg = "#393649",
          nontext = "#3b4048",
          white = "#f8f8f2",
          black = "#7970a9",
        },
        show_end_of_buffer = true,
        transparent_bg = true,
        italic_comment = true,
      })
    end,
  },
  {
    'jakewvincent/mkdnflow.nvim',
    dependecies = {
      rocks = 'luautf8',
      "ekickx/clipboard-image.nvim",
      "davidgranstrom/nvim-markdown-preview",
    },
    lazy = false,
    config = function()
      require('mkdnflow').setup()
    end
  },
  {
    "utilyre/barbecue.nvim",
    name = "barbecue",
    version = "*",
    lazy = false,
    dependencies = {
      "SmiteshP/nvim-navic",
      "nvim-tree/nvim-web-devicons", -- optional dependency
    },
    opts = {
      -- configurations go here
    },
  },
  {
    "iamcco/markdown-preview.nvim",
    build = "cd app && npm install",
    ft = "markdown",
    config = function()
      vim.g.mkdp_auto_start = 1
    end,
  },
  {
    "williamBoman/mason-lspconfig.nvim",
    dependencies = {
      "williamboman/mason.nvim",
      "neovim/nvim-lspconfig"
    },
    opts = {
      ensure_installed = {
        "lua-language-server",
        "html-lsp",
        "prettier",
        "stylua",
        "json-language-server",
        "ansible-language-server",
        "gradle-language-server",
        "tflint",
        "sqlls",
        "python-lsp-server",
        "helm-ls",
        "yaml-language-server",
        "terraform-ls",
      },
    },
  },
  {
    "nvim-treesitter/nvim-treesitter",
    opts = {
      ensure_installed = {
        -- defaults 
        "vim",
        "lua",

        -- web dev 
        "html",
        "css",
        "javascript",
        "typescript",
        "tsx",
        "json",
        -- "vue", "svelte",

       -- low level
        "c",
        "zig",
        "python",
        "rust",
        "java",

        -- DevOps
        "dockerfile",
        "markdown",
        "markdown_inline",
        "terraform",
        "yaml",
        "groovy",
        "go",
      },
    },
  },
  {
    "kdheepak/lazygit.nvim",
    -- optional for floating window border decoration
    lazy = false,
    dependencies = {
      "nvim-lua/plenary.nvim",
    },
  },
}
return plugins
