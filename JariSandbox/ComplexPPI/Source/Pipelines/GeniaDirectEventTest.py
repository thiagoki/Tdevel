# This file shows a possible pipeline, that resembles the Shared Task.
# It uses the mini-subsets of the Shared Task files, which are faster 
# to process and thus enable rapid testing of the system.

# most imports are defined in Pipeline
from Pipeline import *

# define shortcuts for commonly used files
FULL_TRAIN_FILE="/usr/share/biotext/GeniaChallenge/xml/train.xml"
if False: # mini
    TRAIN_FILE="/usr/share/biotext/GeniaChallenge/xml/train-with-duplicates-mini.xml"
    TEST_FILE="/usr/share/biotext/GeniaChallenge/xml/devel-with-duplicates-mini.xml"
    EMPTY_TEST_FILE="/usr/share/biotext/GeniaChallenge/xml/devel-with-duplicates-mini-empty.xml"
    EXPERIMENT_NAME="GeniaDirectEventTest"
    CSC_ACCOUNT="jakrbj@louhi.csc.fi"
    MEMORY=4194304
    CORES=1
else:
    TRAIN_FILE="/usr/share/biotext/GeniaChallenge/xml/train-with-duplicates.xml"
    TEST_FILE="/usr/share/biotext/GeniaChallenge/xml/devel-with-duplicates.xml"
    EMPTY_TEST_FILE="/usr/share/biotext/GeniaChallenge/xml/devel-with-duplicates-empty.xml"
    EXPERIMENT_NAME="GeniaDirectEventTestFull"
    CSC_ACCOUNT="jakrbj@murska.csc.fi"
    MEMORY=8000000
    CORES=4

#EDGE_CLASSIFIER_PARAMS="c:1,1000,100000,500000"
EDGE_CLASSIFIER_PARAMS="c:1,10,100,1000,10000,100000,500000,1000000,5000000,10000000,50000000,100000000,1000000000"

#EDGE_CLASSIFIER_PARAMS="c:10000000,50000000,100000000,1000000000"#"c:10000,28000,50000"
#EDGE_CLASSIFIER_PARAMS="c:1,10,100,1000,10000,100000,500000,1000000,5000000,10000000"#"c:10000,28000,50000"
#EDGE_CLASSIFIER_PARAMS="c:0.00001,0.0001,0.001,0.01,0.1,1,10,100"#"c:10000,28000,50000"
optimizeLoop = True # search for a parameter, or use a predefined one
WORKDIR="/usr/share/biotext/EventExtension/DirectEvents/" + EXPERIMENT_NAME
CSC_WORKDIR = os.path.join("CSCConnection",WORKDIR.lstrip("/"))
PARSE_TOK="split-McClosky"

# These commands will be in the beginning of most pipelines
workdir(WORKDIR, False) # Select a working directory, don't remove existing files
log() # Start logging into a file in working directory

goldPassThrough = False
if goldPassThrough: # gold pass-through test
    MyCls = ACCls
else:
    MyCls = Cls

###############################################################################
# Trigger detection
###############################################################################
# The gazetteer will increase example generator speed, and is supposed not to
# reduce performance. The gazetteer is built from the full training file,
# even though the mini-sets are used in the slower parts of this demonstration
# pipeline.
if False:
    PathGazetteer.build(FULL_TRAIN_FILE, "path-gazetteer-train", PARSE_TOK, includeNeg=False)
    Gazetteer.run(FULL_TRAIN_FILE, "gazetteer-train", PARSE_TOK, "headOffset", includeNeg=False, stem=True)

###############################################################################
# Edge detection
###############################################################################
if False:
    #EDGE_FEATURE_PARAMS="style:typed,directed,entities,genia_limits,noMasking,maxFeatures"
    EDGE_FEATURE_PARAMS="style:typed,directed,no_linear,entities,genia_limits,noMasking,maxFeatures,stem_gazetteer"
        
    # Build examples, see trigger detection
    DirectEventExampleBuilder.run(TEST_FILE, "event-test-examples", PARSE_TOK, PARSE_TOK, EDGE_FEATURE_PARAMS, "genia-direct-event-ids", "gazetteer-train", "path-gazetteer-train")
    if True:
        DirectEventExampleBuilder.run(TRAIN_FILE, "event-train-examples", PARSE_TOK, PARSE_TOK, EDGE_FEATURE_PARAMS, "genia-direct-event-ids", "gazetteer-train", "path-gazetteer-train", 0.4) #1.0)
        DirectEventExampleBuilder.run(EMPTY_TEST_FILE, "event-test-empty-examples", PARSE_TOK, PARSE_TOK, EDGE_FEATURE_PARAMS, "genia-direct-event-ids", "gazetteer-train", "path-gazetteer-train")
    # Run the optimization loop. Note that here we must optimize against the gold
    # standard examples, because we do not know real classes of edge examples built between
    # predicted triggers

if True:
    STEv.setOptions("delme", 1, TEST_FILE, PARSE_TOK, PARSE_TOK)
    if goldPassThrough:
        c = None
    else:
        c = CSCConnection(CSC_WORKDIR, CSC_ACCOUNT, False, memory=MEMORY, cores=CORES)
    best = optimize(MyCls, STEv, "event-train-examples", "event-test-examples",\
        "genia-direct-event-ids.class_names", EDGE_CLASSIFIER_PARAMS, "event-param-opt", None, c)
    print "Evaluating examples built on empty test file"
    MyCls.test("event-test-empty-examples", best[1], "event-test-empty-classifications")
    STEv.evaluate("event-test-empty-examples", "event-test-empty-classifications", "genia-direct-event-ids.class_names")
    
if False:
    best = [None,None,"event-test-empty-classifications"]
    #best = [None,None,"event-param-opt/predictions-c_1000000"]
    # Write the predicted edges to an interaction xml which has predicted triggers.
    # This function handles both trigger and edge example classifications
    edgeXml = ExampleUtils.writeToInteractionXML("event-test-empty-examples", best[2], TEST_FILE, None, "genia-direct-event-ids.class_names", PARSE_TOK, PARSE_TOK)
    # Split overlapping, merged elements (e.g. "Upregulate---Phosphorylate")
    #ix.splitMergedElements(edgeXml)
    ## Always remember to fix ids
    ix.recalculateIds(edgeXml, None, True)
    writeXML(edgeXml, "test-predicted-events.xml")
    # EvaluateInteractionXML differs from the previous evaluations in that it can
    # be used to compare two separate GifXML-files. One of these is the gold file,
    # against which the other is evaluated by heuristically matching triggers and
    # edges. Note that this evaluation will differ somewhat from the previous ones,
    # which evaluate on the level of examples.
    EvaluateInteractionXML.run(Ev, "test-predicted-events.xml", TEST_FILE, PARSE_TOK, PARSE_TOK)
    gifxmlToGenia("test-predicted-events.xml", "geniaformat", 1)
    evaluateSharedTask("geniaformat", 1)

if False:
    STEv.setOptions("delme", 1, TEST_FILE, PARSE_TOK, PARSE_TOK)
    STEv.evaluate("event-test-empty-examples", "event-test-empty-classifications", "genia-direct-event-ids.class_names")
