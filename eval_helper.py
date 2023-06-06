import numpy as np
from root_to_numpy import *
from tensorflow import keras
from tensorflow import saved_model
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import MinMaxScaler
#from sklearn.preprocessing import MaxAbsScaler
from plot_helper import *
from models import *

def getTwoJetSystem(x_events,y_events):
    
    track_array0 = ["jet0_GhostTrack_pt", "jet0_GhostTrack_eta", "jet0_GhostTrack_phi", "jet0_GhostTrack_e", "jet0_GhostTrack_z0", "jet0_GhostTrack_d0", "jet0_GhostTrack_qOverP"]
    track_array1 = ["jet1_GhostTrack_pt", "jet1_GhostTrack_eta", "jet1_GhostTrack_phi", "jet1_GhostTrack_e", "jet1_GhostTrack_z0", "jet1_GhostTrack_d0", "jet1_GhostTrack_qOverP"]
    jet_array = ["jet1_eta", "jet1_phi", "jet2_eta", "jet2_phi"]
    bkg_in0 = read_vectors("../v8.1/user.ebusch.QCDskim.mc20e.root", x_events, track_array0, use_weight=True)
    sig_in0 = read_vectors("../v8.1/user.ebusch.SIGskim.mc20e.root", y_events, track_array0, use_weight=False)
    bkg_in1 = read_vectors("../v8.1/user.ebusch.QCDskim.mc20e.root", x_events, track_array1, use_weight=True)
    sig_in1 = read_vectors("../v8.1/user.ebusch.SIGskim.mc20e.root", y_events, track_array1, use_weight=False)
    jet_bkg = read_flat_vars("../v8.1/user.ebusch.QCDskim.mc20e.root", x_events, jet_array, use_weight=True)
    jet_sig = read_flat_vars("../v8.1/user.ebusch.SIGskim.mc20e.root", y_events, jet_array, use_weight=False)
    #mT_bkg = read_flat_vars("../v8.1/user.ebusch.SIGskim.mc20e.root", x_events, ["mT_jj"], use_weight=False)

    _, _, bkg_nz0 = apply_TrackSelection(bkg_in0, jet_bkg)
    _, _, sig_nz0 = apply_TrackSelection(sig_in0, jet_sig)
    _, _, bkg_nz1 = apply_TrackSelection(bkg_in1, jet_bkg)
    _, _, sig_nz1 = apply_TrackSelection(sig_in1, jet_sig)
    
    bkg_nz = bkg_nz0 & bkg_nz1
    sig_nz = sig_nz0 & sig_nz1

    # select events which have both valid leading and subleading jet tracks
    bkg_pt0 = bkg_in0[bkg_nz]
    bkg_pt1 = bkg_in1[bkg_nz]
    sig_pt0 = sig_in0[sig_nz]
    sig_pt1 = sig_in1[sig_nz]
    bjet_sel = jet_bkg[bkg_nz]
    sjet_sel = jet_sig[sig_nz]
    #mT_sel = mT_bkg[bkg_nz]

    plot_nTracks(bkg_pt0, sig_pt0, "j1")
    plot_nTracks(bkg_pt1, sig_pt1, "j2")

    bkg_sel = np.concatenate((bkg_pt0,bkg_pt1),axis=1)
    sig_sel = np.concatenate((sig_pt0,sig_pt1),axis=1)

    #bkg_sel = pt_sort(bkg_sel)
    #sig_sel = pt_sort(sig_sel)
    plot_nTracks(bkg_sel, sig_sel, "jAll")

    bkg = apply_JetScalingRotation(bkg_sel, bjet_sel,0)
    sig = apply_JetScalingRotation(sig_sel, sjet_sel,0)

    #plot
    #x_sel_nz = remove_zero_padding(bkg_sel)
    #sig_sel_nz = remove_zero_padding(sig_sel)
    #plot_vectors(bkg_sel,sig_sel,"PFNraw")
    #x_nz = remove_zero_padding(bkg)
    #sig_nz = remove_zero_padding(sig)
    #plot_vectors(x_nz,sig_nz,"AErotated_avg")

    #x_2D,scaler = apply_StandardScaling(bkg)
    #sig_2D,_ = apply_StandardScaling(sig, scaler, False)
    #sig_2D,_ = apply_StandardScaling(sig)
    #x = bkg
    #sig = sig

    print(bkg.shape)
    print(sig.shape)
    #print(mT_sel.shape)
    #x = x_2D.reshape(bkg.shape[0],x_2D.shape[1]*4)
    #sig = sig_2D.reshape(sig_2D.shape[0],x_2D.shape[1]*4)
    #plot_vectors(remove_zero_padding(x_2D),remove_zero_padding(sig_2D),"AEscaled")
    #plot_vectors(x,sig,"AEWithZeroRotated")
    return bkg, sig

def check_weights(x_events):
    bkg_nw = read_flat_vars("../v8.1/user.ebusch.QCDskim.mc20e.root", x_events, ["jet1_pt"], use_weight=False)
    bkg_w = read_flat_vars("../v8.1/user.ebusch.QCDskim.mc20e.root", x_events, ["jet1_pt"], use_weight=True)
    sig_nw = read_flat_vars("../v8.1/user.ebusch.SIGskim.mc20e.root", x_events, ["jet1_pt"], use_weight=False)
    plot_single_variable([bkg_nw,bkg_w, sig_nw], ["QCD No Weights", "QCD Weights", "SIG No Weights"], "QCD Weight Check", logy=True) 

def get_dPhi(x1,x2):
    dPhi = x1 - x2
    if(dPhi > 3.14):
        dPhi -= 2*3.14
    elif(dPhi < -3.14):
        dPhi += 2*3.14
    return dPhi

def remove_zero_padding(x):
    #x has shape (nEvents, nSteps, nFeatures)
    #x_out has shape (nEvents, nFeatures)
    x_nz = np.any(x,axis=2) #find zero padded steps
    x_out = x[x_nz]

    return x_out

def reshape_3D(x, nTracks, nFeatures):
    print(x[4])
    x_out = x.reshape(x.shape[0],nTracks,nFeatures)
    print(x_out[4])
    return x_out

def pt_sort(x):
    for i in range(x.shape[0]):
        ev = x[i]
        x[i] = ev[ev[:,0].argsort()]
    #y = x[:,-60:,:]
    return x

def apply_TrackSelection(x_raw, jets):
    x = np.copy(x_raw)
    x[x[:,:,0] < 10] = 0 # apply pT requirement
    print("Input track shape: ", x.shape)
    # require at least 3 tracks
    x_nz = np.array([len(jet.any(axis=1)[jet.any(axis=1)==True]) >= 3 for jet in x])
    x = x[x_nz]
    jets = jets[x_nz]
    print("Selected track shape: ", x.shape)
    print("Selected jet shape: ", jets.shape)
    print()
    return x, jets, x_nz

def apply_StandardScaling(x_raw, scaler=MinMaxScaler(), doFit=True):
    x= np.zeros(x_raw.shape)
    
    x_nz = np.any(x_raw,axis=len(x_raw.shape)-1) #find zero padded events 
    x_scale = x_raw[x_nz] #scale only non-zero jets
    #scaler = StandardScaler()
    if (doFit): scaler.fit(x_scale) 
    x_fit = scaler.transform(x_scale) #do the scaling
    
    x[x_nz]= x_fit #insert scaled values back into zero padded matrix
    
    return x, scaler

def apply_EventScaling(x_raw):
    
    x = np.copy(x_raw) #copy

    x_totals = x_raw.sum(axis=1) #get sum total pt, eta, phi, E for each event
    x[:,:,0] = (x_raw[:,:,0].T/x_totals[:,0]).T  #divide each pT entry by event pT total
    x[:,:,3] = (x_raw[:,:,3].T/x_totals[:,3]).T  #divide each E entry by event E total

    return x

def apply_JetScalingRotation(x_raw, jet, jet_idx):
   
    if (x_raw.shape[0] != jet.shape[0]):
        print("Track shape", x_raw.shape, "is incompatible with jet shape", jet.shape)
        print("Exiting...")
        return
    
    x = np.copy(x_raw) #copy
    x_totals = x_raw.sum(axis=1) #get sum total pt, eta, phi, E for each event
    x[:,:,0] = (x_raw[:,:,0].T/x_totals[:,0]).T  #divide each pT entry by event pT total
    x[:,:,3] = (x_raw[:,:,3].T/x_totals[:,3]).T  #divide each E entry by event E total
    
    #jet_phi_avs = np.zeros(x.shape[0])
    for e in range(x.shape[0]):
        jet_eta_av = (jet[e,0] + jet[e,2])/2.0 
        jet_phi_av = (jet[e,1] + jet[e,3])/2.0 
        #jet_phi_avs[e] = jet_phi_av
        for t in range(x.shape[1]):
            if not x[e,t,:].any():
                #print(x[e,t,:])
                continue
            #if not jet[e,jet_idx,:].any():
            #    x[e,t,:] = 0
            else:
                x[e,t,1] = x_raw[e,t,1] - jet_eta_av # subtrack subleading jet eta from each track
                x[e,t,2] = get_dPhi(x_raw[e,t,2],jet_phi_av) # subtrack subleading jet phi from each track
                #x[e,t,1] = x_raw[e,t,1] - jet[e,jet_idx,0] # subtrack subleading jet eta from each track
                #x[e,t,2] = get_dPhi(x_raw[e,t,2],jet[e,jet_idx,1]) # subtrack subleading jet phi from each track
    #plt.hist(jet_phi_avs)
    #plt.show()
    return x


def get_multi_loss(model_svj, x_test, y_test):
    bkg_total_loss = []
    sig_total_loss = []
    bkg_kld_loss = []
    sig_kld_loss = []
    bkg_reco_loss = []
    sig_reco_loss = []
    nevents = min(len(y_test),len(x_test))
    step_size = 4
    for i in range(0,nevents, step_size):
        xt = x_test[i:i+step_size]
        yt = y_test[i:i+step_size]
      
        # NOTE - unclear why they are printed in this order, but it seems to be the case
        x_loss,x_reco,x_kld = model_svj.evaluate(xt, batch_size = step_size, verbose=0)
        y_loss,y_reco,y_kld = model_svj.evaluate(yt, batch_size = step_size, verbose=0)
      
        bkg_total_loss.append(x_loss)
        sig_total_loss.append(y_loss)
        bkg_kld_loss.append(x_kld)
        sig_kld_loss.append(y_kld)
        bkg_reco_loss.append(x_reco)
        sig_reco_loss.append(y_reco)
        if i%100 == 0: print("Processed", i, "events")

    return bkg_total_loss, sig_total_loss, bkg_kld_loss, sig_kld_loss, bkg_reco_loss, sig_reco_loss

def get_single_loss(model_svj, x_test, y_test):
    bkg_loss = []
    sig_loss = []
    nevents = min(len(y_test),len(x_test))
    step_size = 4
    for i in range(0,nevents, step_size):
        xt = x_test[i:i+step_size]
        yt = y_test[i:i+step_size]
    
        x_loss = model_svj.evaluate(xt, batch_size = step_size, verbose=0)
        y_loss = model_svj.evaluate(yt, batch_size = step_size, verbose=0)
        
        bkg_loss.append(x_loss)
        sig_loss.append(y_loss)
        if i%100 == 0: print("Processed", i, "events")

    return bkg_loss, sig_loss

def transform_loss(bkg_loss, sig_loss, make_plot=False, plot_tag=''):
    nevents = len(sig_loss)
    truth_sig = np.ones(nevents)
    truth_bkg = np.zeros(nevents)
    truth_labels = np.concatenate((truth_bkg, truth_sig))
    eval_vals = np.concatenate((bkg_loss,sig_loss))
    eval_min = min(eval_vals)
    eval_max = max(eval_vals)-eval_min
    eval_transformed = [(x - eval_min)/eval_max for x in eval_vals]
    bkg_transformed = [(x - eval_min)/eval_max for x in bkg_loss]
    sig_transformed = [(x - eval_min)/eval_max for x in sig_loss]
    if make_plot:
        plot_score(bkg_transformed, sig_transformed, False, False, plot_tag+'_Transformed')
    return truth_labels, eval_vals 

def transform_loss_ex(bkg_loss, sig_loss, make_plot=False, plot_tag=''):
    nevents = len(sig_loss)
    eval_vals = np.concatenate((bkg_loss,sig_loss))
    eval_transformed = [1 - np.exp(-x) for x in eval_vals]
    bkg_transformed = [1 - np.exp(-x) for x in bkg_loss]
    sig_transformed = [1 - np.exp(-x) for x in sig_loss]
    if make_plot:
        plot_score(bkg_transformed, sig_transformed, False, False, plot_tag+'_TransformedEx')
    return eval_vals 

def vrnn_transform(bkg_loss, sig_loss, make_plot=False, plot_tag=''):
    train_mean = np.mean(bkg_loss)
    bkg_loss_p = [1-x/(2*train_mean) for x in bkg_loss]
    sig_loss_p = [1-x/(2*train_mean) for x in sig_loss]
    if make_plot:
        plot_score(bkg_loss_p, sig_loss_p, False, False, plot_tag+'_MeanShift')
    return bkg_loss_p, sig_loss_p    

def getSignalSensitivityScore(bkg_loss, sig_loss, percentile=95):
    nSigAboveThreshold = np.sum(sig_loss > np.percentile(bkg_loss, percentile))
    return nSigAboveThreshold / len(sig_loss)

def applyScoreCut(loss,test_array,cut_val):
    return test_array[loss>cut_val] 

def do_roc(bkg_loss, sig_loss, plot_tag, make_transformed_plot=False):
    truth_labels, eval_vals = transform_loss(bkg_loss, sig_loss, make_plot=make_transformed_plot, plot_tag=plot_tag) 
    fpr, tpr, trh = roc_curve(truth_labels, eval_vals) #[fpr,tpr]
    auc = roc_auc_score(truth_labels, eval_vals)
    print("AUC - "+plot_tag+": ", auc)
    make_roc(fpr,tpr,auc,plot_tag)
    make_sic(fpr,tpr,auc,plot_tag)
    return auc

