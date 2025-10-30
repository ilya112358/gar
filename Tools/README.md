# Gait Data Preparation for GAR

Scripts for exporting data from **Visual3D** and packaging it for import into the **Interactive Gait Analysis Report (GAR)**.

---

## 📄 Files
- **GaitDataPrep.bat** – runs Visual3D, executes the export pipeline, and creates `GaitData.zip`.
- **ExportForGAR.v3s** – Visual3D pipeline specifying which data are exported.

---

## ⚙️ How to Use

1. Make sure your Visual3D project (`.cmz`) was created via the **Clinical Gait PAF / Visual3D Analysis** workflow in **Qualisys Track Manager (QTM)**.

2. Run the batch file in Command Prompt with full paths to your `.cmz` and the `.v3s` script (right-click → Copy as path in Explorer):

   ```cmd
   GaitDataPrep.bat "C:\Users\User\Documents\Clinical Gait 2.1.5.773\Data\Doe_Jim_2017-04-12_0002\2017-04-12\IOR - Full body_Barefoot\Report_0002_Doe_Barefoot_2017-04-12.cmz" "C:\Users\User\Documents\Programming\gar\Tools\ExportForGAR.v3s"
   ```

3. The batch will produce **`GaitData.zip`** in the same directory as the `.cmz`.

4. Upload **`GaitData.zip`** on the **_Measurement_** page of the **GAR** app for interactive analysis.

---

## 💡 Notes
- Requires a valid installation of **Visual3D** (check `Visual3D.exe` path inside the batch).
- Each run overwrites the previous `GaitData.zip`.
- To change export contents, edit `ExportForGAR.v3s`.
