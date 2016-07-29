import sys
import os
import pandas as pd
import subprocess
import argparse
import pdb
import pickle
from eis import setup_environment

"""
Code to take top performing recent models and
put them in the evaluation webapp for further
examination.

Examples:
--------
python prepare.py '2016-07-28' auc_score
python prepare.py '2016-07-28' precision_score_at_top_point_01_percent
"""

engine, config = setup_environment.get_database()
try:
    con = engine.raw_connection()
    con.cursor().execute("SET SCHEMA '{}'".format('models'))
except:
    pass


def get_metric_best_models(timestamp, metric):

    """
    Get the evaluation results of the best recent models
    by the specified timestamp and given metric
    """

    query   =  ("   SELECT {} FROM results.evaluations JOIN results.models \
                    ON evaluations.model_id=models.model_id \
                    WHERE run_time >= '{}' \
                    AND {} is not null \
                    ORDER BY {} DESC LIMIT 25; ").format(metric, timestamp, metric, metric)

    df_models = pd.read_sql(query, con=con)
    output = df_models[metric].apply(lambda x: str(x)).values
    statement = "Resulting metric for models with best {} run on or after {}: \n".format(metric, timestamp)
    print (statement, output)
    return output


def get_best_recent_models(timestamp, metric):
    """
    Get the model id of the best recent models
    by the specified timestamp and given metric
    """

    query   =  ("   SELECT run_time FROM results.evaluations JOIN results.models \
                    ON evaluations.model_id=models.model_id \
                    WHERE run_time >= '{}' \
                    AND {} is not null \
                    ORDER BY {} DESC LIMIT 25; ").format(timestamp, metric, metric)

    df_models = pd.read_sql(query, con=con)
    output = df_models['run_time'].apply(lambda x: str(x).replace(' ', 'T')).values
    return output


def get_best_models(metric):
    """
    Grab the identifiers of the best performing (top AUC) models
    from the database.
    """
    #query = "SELECT id_timestamp FROM models.full ORDER BY auc DESC LIMIT 25"
    query   =  ("   SELECT run_time FROM results.evaluations JOIN results.models \
                    ON evaluations.model_id=models.model_id \
                    WHERE {} is not null \
                    ORDER BY {} DESC LIMIT 25; ").format(metric, metric)

    df_models = pd.read_sql(query, con=con)
    output = df_models['run_time'].apply(lambda x: str(x).replace(' ', 'T')).values
    return output


def get_pickel_best_models(timestamp, metric):

    """
    Get the pickle file of the best recent models
    by the specified timestamp and given metric

    Dumps top pickle files from database to results directory.
    """

    query   =  ("   SELECT pickle_file, run_time FROM results.evaluations JOIN results.models \
                    ON evaluations.model_id=models.model_id \
                    WHERE run_time >= '{}' \
                    AND {} is not null \
                    ORDER BY {} DESC LIMIT 25; ").format(timestamp, metric, metric)

    df_models = pd.read_sql(query, con=con)
    N = len(df_models['pickle_file'])

    for file_number in range(0, N):
        pickle_file = pickle.loads(df_models['pickle_file'].iloc[file_number])
        file_name = df_models['run_time'].apply(lambda x: str(x).replace(' ', 'T')).iloc[file_number]
        full_file_name = "police_eis_results_"+"top_"+metric+"_"+file_name+".pkl"
        file_path = "results/"+full_file_name
        pickle.dump(pickle_file, open( file_path, "wb" ) )

    return None


def prepare_webapp_display(ids, src_dir, dest_dir):
    """
    Move the relevant webapp files into the directory that the evaluation
    webapp pulls from.
    """
    for model in ids:
        filename = '{}police_eis_results_{}.pkl'.format(src_dir, model)
        subprocess.check_output(["cp", filename, dest_dir])
    return None


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("timestamp", type=str, help="show models more recent than a given timestamp")
    parser.add_argument("metric", type=str, help="specify a desired metric to optimize")
    args = parser.parse_args()

    print("[*] Updating model list...")
    metrics = get_metric_best_models(args.timestamp, args.metric)
    print("[*] Dumping requested pickle files to results...")
    pickles = get_pickel_best_models(args.timestamp, args.metric)
    print("[*] Done!")