import numpy as np
import json
from root_to_numpy import *
from tensorflow import keras
from tensorflow import saved_model
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from joblib import dump, load
from plot_helper import *
from models import *
from models_archive import *
from eval_helper import *
import h5py
import sys
from termcolor import cprint
## ---------- Load graph model ----------
def call_functions(x_events,y_events, tag, bool_weight, extraVars):
  graph = keras.models.load_model(arch_dir+pfn_model+'_graph_arch')
  graph.load_weights(arch_dir+pfn_model+'_graph_weights.h5')
  graph.compile()

## Load classifier model
  classifier = keras.models.load_model(arch_dir+pfn_model+'_classifier_arch')
  classifier.load_weights(arch_dir+pfn_model+'_classifier_weights.h5')
  classifier.compile()

## Load history
# with open(arch_dir+ae_model+"_history.json", 'r') as f:
#     h = json.load(f)
# print(h)
# print(type(h))

  print ("Loaded model")

  bkg2, sig2, mT_bkg, mT_sig = getTwoJetSystem(x_events,y_events,tag_file=tag, tag_title=tag, bool_weight=bool_weight,  extraVars=my_variables)
#bkg2, sig2, mT_bkg, mT_sig = getTwoJetSystem(x_events,y_events, ["mT_jj"])
  scaler = load(arch_dir+pfn_model+'_scaler.bin')
  bkg2,_ = apply_StandardScaling(bkg2,scaler,False)
  sig2,_ = apply_StandardScaling(sig2,scaler,False)
# plot_vectors(bkg2,sig2,"PFN")

  phi_bkg = graph.predict(bkg2)
  phi_sig = graph.predict(sig2)

# each event has a pfn score 
  pred_phi_bkg = classifier.predict(phi_bkg)
  pred_phi_sig = classifier.predict(phi_sig)

# write on html


## Classifier loss
  bkg_loss = pred_phi_bkg[:,1]
  sig_loss = pred_phi_sig[:,1]
  """
  cprint('sig_loss', 'blue')
  cprint(sig_loss, 'blue')
  cprint('mT_sig', 'blue')
  cprint(mT_sig, 'blue')
  """
  my_variables.insert(0,"score")
  save_bkg = np.concatenate((bkg_loss[:,None], mT_bkg),axis=1)
  save_sig = np.concatenate((sig_loss[:,None], mT_sig),axis=1)
  ds_dt = np.dtype({'names':my_variables,'formats':[(float)]*len(my_variables)})
  rec_bkg = np.rec.array(save_bkg, dtype=ds_dt)
  rec_sig = np.rec.array(save_sig, dtype=ds_dt)
  
  return rec_bkg, rec_sig

## ---------- USER PARAMETERS ----------
## Model options:
##    "AE", "VAE", "PFN_AE", "PFN_VAE"
pfn_model = 'PFN'
#pfn_model = 'PFNv1'
#arch_dir = "/data/users/ebusch/SVJ/autoencoder/svj-vae/architectures_saved/"
## Load testing data
x_events = 2464544
y_events = 631735
#x_events = 50000
#y_events = 50000
bool_weight=True
if bool_weight:weight_tag='ws'
else:weight_tag='nws'
tag= f'{pfn_model}_2jAvg_MM_{weight_tag}_xNE={x_events}_yNE={y_events}'
#tag= f'{pfn_model}_2jAvg_MM_{weight_tag}_NE={x_events}'
#tag= f'{pfn_model}_2jAvg_MM_{weight_tag}'
my_variables= ["mT_jj", "jet1_pt", "jet2_pt", "jet1_Width", "jet2_Width", "jet1_NumTrkPt1000PV", "jet2_NumTrkPt1000PV", "met_met", "mT_jj_neg", "rT", "maxphi_minphi", "dphi_min", "pt_balance_12", "dR_12", "deta_12", "dphi_12", "weight", "mcEventWeight"]
#my_variables=["mT_jj"]
bool_rewrite=False
#bool_rewrite=True
h5dir='h5dir/'
filename_bkg=f'{tag}_bkg'
filename_sig=f'{tag}_sig'
h5path_bkg=h5dir+filename_bkg+'.h5'
h5path_sig=h5dir+filename_sig+'.h5'
#arch_dir="architectures_saved_old/architectures_saved_jun5/"
arch_dir="architectures_saved/"
data_bkg={}
data_sig={}
if bool_rewrite or (not(os.path.exists(h5path_bkg)) or not(os.path.exists(h5path_sig))):
  print('will write files b/c the files donot exist or bool_rewrite is set to be True'+ h5path_bkg+ h5path_sig)
  rec_bkg, rec_sig=call_functions(x_events,y_events, tag, bool_weight=bool_weight, extraVars=my_variables)
  with h5py.File(h5path_bkg, 'w') as f:
    ar_bkg = f.create_dataset("default", data = rec_bkg)
  with h5py.File(h5path_sig, 'w') as f:
    ar_sig = f.create_dataset("default", data = rec_sig)

else:print('both exist and not rewrite')
# read the files anyway even after writing b/c otherwise throws an error that it's not a dataset
with h5py.File(h5path_bkg, 'r') as f:
#    data_bkg = f["default"]['mT_jj'][()]
  for var in my_variables+["score"]:
#    data_bkg = f["default"][()]
    ar=f["default"][var]
    data_bkg[var] = ar[:,0]
  print(h5path_bkg)
  print('hi')
with h5py.File(h5path_sig, 'r') as f:
  for var in my_variables+["score"]:
    ar=f["default"][var]
    data_sig[var] = ar[:,0]
  print(h5path_sig)
   
#  data_bkg=f["default"][()]
#  data_sig=f["default"][()]
####################################
#"""
#"""
print(data_bkg)
#data_bkg=np.array(data_bkg)
#data_bkg2=data_bkg2
#print(data_bkg['mT_jj'][:,0],data_bkg['mT_jj'].size)


#bkg_loss=data_bkg[0,None]
#sig_loss=data_sig[0,None]
#var_bkg=data_bkg[0,None]
"""
save_bkg = np.concatenate((bkg_loss[:,None], mT_bkg),axis=1)
save_sig = np.concatenate((sig_loss[:,None], mT_sig),axis=1)
"""

#cut on each event depending on a pfn score
#find which score gives us signal to percentile of background
#percentile_ls=[20, 30, 60, 100]

"""percentile_ls=[0, 0.5, 5, 20]
cuts=[]
for percentile in percentile_ls:
  score = getSignalSensitivityScore(data_bkg['score'], data_sig['score'], percentile=100-percentile)
  #score = getSignalSensitivityScore(bkg_loss, sig_loss, percentile=percentile)
  cuts.append(round(score,3))
print(f'{percentile}% -score {score}')
"""
def equal_length(bkg_loss, sig_loss):
  if (len(bkg_loss) > len(sig_loss)): # necessary when computing AUC score
    bkg_loss = bkg_loss[:len(sig_loss)]
#    mT_bkg=mT_bkg[:len(sig_loss)] # added
  else:
    sig_loss = sig_loss[:len(bkg_loss)]
#    mT_sig=mT_sig[:len(sig_loss)] # added
  return bkg_loss,sig_loss
bkg_loss,sig_loss=equal_length(bkg_loss=data_bkg['score'],sig_loss=data_sig['score'])
make_transformed_plot=False
auc=do_roc(bkg_loss, sig_loss, tag_file=tag, tag_title=tag, make_transformed_plot=make_transformed_plot)

cuts=[0, .6,.9,.98] 
for key in data_bkg:
  bkg_ls=[]
  bkg_weight_ls=[]
  bkg_loss_arr=np.array(data_bkg['score'])
  for i, cut in enumerate(cuts):
    bkg_cut_idx=np.argwhere(bkg_loss_arr>=cut)
    bkg_cut=data_bkg[key][bkg_cut_idx]  
    bkg_cut_weight=data_bkg['weight'][bkg_cut_idx]  
#  bkg_cut=bkg_loss_arr[bkg_cut_idx]
    bkg_cut=bkg_cut.flatten()
    print(i, cut, len(bkg_cut))
    bkg_ls.append(bkg_cut)
    bkg_weight_ls.append(bkg_cut_weight)
#plot mT distribution
#plot_single_variable([bkg_loss_arr,bkg_cut], cuts, "mT distribution", logy=True) 
  plot_single_variable(bkg_ls, cuts,title= f"{key} distribution",weights_ls=bkg_weight_ls, density_top=True,logy=True)
 

#plot_single_variable([bkg_loss,sig_loss], ["Background", "Signal"], "mT distribution", logy=True) 
print('done')
##  #--- Grid test
##  scores = np.zeros((10,4))
##  aucs = np.zeros((10,4))
##  j = -1
##  for i in range(487,527):
##    k = i%4-3
##    if k == 0: j+=1
##    if i in [488,511,514,517,520,522]:continue
##    sig_raw = read_vectors("../v6.4/user.ebusch.515"+str(i)+".root", nevents)
##    sig = apply_EventScaling(sig_raw)
##    phi_sig = graph.predict(sig)
##    pred_phi_sig = ae.predict(phi_sig)['reconstruction']
##    sig_loss = keras.losses.mse(phi_sig, pred_phi_sig)
##  
##    score = getSignalSensitivityScore(bkg_loss, sig_loss)
##    #print("95 percentile score = ",score)
##    auc = do_roc(bkg_loss, sig_loss, ae_model, False)
##    print(auc,score)
##    scores[j,k] = score
##    aucs[j,k] = auc
##  
##  print(scores)
##  print(aucs)

##  #--- Eval plots 
##  # 1. Loss vs. epoch 
##  plot_saved_loss(h, ae_model, "loss")
##  if model.find('VAE') > -1:
##      plot_saved_loss(h, ae_model, "kl_loss")
##      plot_saved_loss(h, ae_model, "reco_loss")
# 2. Anomaly score
#plot_score(bkg_loss, sig_loss, False, False, ae_model)

#print(mT)
#print(bkg_loss > -11)
#mT_in = mT[bkg_loss > -11]
#print(mT_in)
#plot_score(mT, mT_in, False, False, "mTSel")
#quit()

#transform_loss_ex(bkg_loss, sig_loss, True)
##  #plot_score(bkg_loss, sig_loss, False, True, ae_model+"_xlog")
##  if ae_model.find('VAE') > -1:
##      plot_score(bkg_kl_loss, sig_kl_loss, remove_outliers=False, xlog=True, extra_tag=model+"_KLD")
##      plot_score(bkg_reco_loss, sig_reco_loss, False, False, model_name+'_Reco')
##  # 3. Signal Sensitivity Score
##  score = getSignalSensitivityScore(bkg_loss, sig_loss)
##  print("95 percentile score = ",score)
