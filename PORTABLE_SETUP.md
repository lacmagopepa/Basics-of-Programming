# Beer Game - Portable Setup

This project now includes a **portable Python environment** that runs entirely from the project folder.

## 📁 What's Installed

The `venv` folder contains:
- **Python 3.13** (portable installation)
- **pygame 2.6.1** (game engine)
- **pandas 2.3.3** (data analysis)
- **matplotlib 3.10.8** (visualization)
- **Jupyter Notebook 7.5.1** (analysis notebooks)
- All required dependencies

## 🎮 Running the Game

### Windows:
**Double-click:** `run_game.bat`

### Manual Command:
```cmd
venv\Scripts\activate
python main.py
```

## 📊 Running the Analysis Notebook

### Windows:
**Double-click:** `run_notebook.bat`

This will:
1. Start Jupyter Notebook
2. Open `BeerGame_Analysis.ipynb` in your browser
3. Allow you to view and modify analysis results

### Manual Command:
```cmd
venv\Scripts\activate
jupyter notebook analysis\BeerGame_Analysis.ipynb
```

## 📦 Package Management

### Install new packages:
```cmd
venv\Scripts\activate
pip install package_name
```

### Update requirements.txt:
```cmd
venv\Scripts\activate
pip freeze > requirements.txt
```

### Reinstall all packages:
```cmd
venv\Scripts\activate
pip install -r requirements.txt
```

## 🔧 Portable Installation Benefits

✅ **No system Python required** - Everything runs from the project folder  
✅ **Version locked** - Consistent environment across different machines  
✅ **Easy to share** - Copy the entire folder to another PC and it works  
✅ **Isolated** - Won't conflict with other Python projects  

## 📂 Folder Structure

```
pygame_team_4/
├── venv/                    # Portable Python environment
├── run_game.bat             # Launch the game
├── run_notebook.bat         # Launch Jupyter notebook
├── requirements.txt         # Package dependencies
├── main.py                  # Game entry point
├── analysis/
│   └── BeerGame_Analysis.ipynb  # Analysis notebook
└── ... (other game files)
```

## 🚀 First Time Setup (Already Done!)

The virtual environment is already configured. If you need to recreate it:

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 💡 Tips

- The `venv` folder can be large (~500 MB). Don't commit it to git.
- Use `.gitignore` to exclude `venv/` from version control.
- To move the project, copy the entire folder to a new location.
- The scripts work from any location - just run them from the project folder.

## ⚠️ Troubleshooting

**Game won't start?**
- Make sure you're running from the project folder
- Check that `venv/Scripts/python.exe` exists
- Try reinstalling: `venv\Scripts\pip install --force-reinstall pygame`

**Notebook won't open?**
- Check that Jupyter is installed: `venv\Scripts\jupyter --version`
- Try: `venv\Scripts\activate` then `jupyter notebook`

**Missing packages?**
- Run: `venv\Scripts\pip install -r requirements.txt`
