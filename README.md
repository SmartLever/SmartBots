1. Clone the Project

   - Via HTTPS: `git clone https://github.com/SmartLever/SmartBots.git`
   - via SSH: `git clone https://github.com/SmartLever/SmartBots.git`

2. Navigate into the project's folder

   ```bash
   cd SmartBots/
   ```
   
3. Create Environment

   ```bash
   conda env create -n ebots --file build/conda/conda-3-8-env.yaml
   ```

4. Activate the virtual environment

   ```bash
   conda activate ebots
   ```


5. Install dependencies with poetry

   Install the main dependencies with

   ```bash
   poetry install
   ```
   If you are having trouble with Poetry, use install requirements.txt with pip

   ```bash
   pip install -r requirements.txt
   ```