# **GIT WORKFLOW GUIDE**

You now have:

* 📁 `minipass_env/` → your **main project**  
* 📁 `minipass_env/app/` → your **`dpm` repo as a submodule**, pointing to branch `release-v1.0`

## **1\. Committing and Pushing in `minipass_env` (main project)**

### **✅ Typical workflow:**

`cd ~/Documents/DEV/minipass_env`

`git status`  
`git add .`  
`git commit -m "Your message about changes in minipass_env"`  
`git push`

This will push:

* Any changes to main files (e.g., `docker-compose.yml`, scripts, configs)

* Any update to the submodule commit reference (if the submodule moved to a new commit)  
   

## 

## **2\. Committing and Pushing inside `app/` (your submodule `dpm`)**

`cd ~/Documents/DEV/minipass_env/app`

`git status`  
`git add .`  
`git commit -m "Your message about changes in dpm (submodule)"`

`git push origin release-v1.0`

### **🔁 Then, go back to `minipass_env` and record the new submodule commit:**

`cd ~/Documents/DEV/minipass_env`

`git add app`  
`git commit -m "Update submodule app to latest commit"`  
`git push`

✅ This ensures `minipass_env` always points to the latest version of `app/`. 

## 

## **3\. Cloning the whole thing (for yourself or others)**

To clone `minipass_env` **with the submodule**:

`git clone --recurse-submodules git@github.com:windseeker5/minipass_env.git`

If you forgot `--recurse-submodules`, fix with:

`git submodule update --init --recursive`

