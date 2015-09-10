/**
 * Copyright 2014 Luigi Grimaudo (grimaudo.luigi@gmail.com)
 * 
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package it.polito.dbdmg.searum.rules;

import it.polito.dbdmg.searum.ARM;

import java.io.IOException;
import java.util.Arrays;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Set;

import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.Reducer.Context;
import org.apache.mahout.common.Pair;
import org.apache.mahout.math.map.OpenObjectIntHashMap;
import org.apache.mahout.common.Parameters;

/**
 * 
 * @author Luigi Grimaudo
 * @version 0.0.1 mine a rules for each itemset and compute quality measure.
 * 
 *          Note: Mine only rule with a single items as consequence to compute
 *          the lift without too much overhead
 * 
 */
public class RuleMiningReducer extends Reducer<Text, Text, Text, Text> {

    private final HashMap<String, Long> freqItemMap = new HashMap<String, Long>();
    private Double minConfidence;

    @Override
    protected void reduce(Text key, Iterable<Text> values, Context context)
            throws IOException, InterruptedException {
        // Key is a premises
        // Value is the complete itemset plus its support

        HashMap<String, Integer> itemsetMap = new HashMap<String, Integer>();
        Double premisesSupport = null;
        String[] premisesComponent = key.toString().split(" ");

        /* Store complete itemset and support */
        for (Text textPattern : values) {
            String stringPattern = textPattern.toString();
            String[] splitPattern = stringPattern.split(",");
            if (splitPattern.length == 1) {
                // Support of premises
                premisesSupport = new Double(new Double(splitPattern[0])
                        / freqItemMap.get("dataset"));
            } else {
                // Complete itemset
                String pattern = splitPattern[0];
                // Support of complete itemset
                Integer support = new Integer(splitPattern[1]);
                itemsetMap.put(pattern, support);
            }
        }

        /* Mine Rule and compute quality measures */
        Double ruleSupport = null;
        Double conclusionSupport = null;
        Double confidence = null;
        Double lift = null;
        for (String itemset : itemsetMap.keySet()) {

            String[] itemsetComponent = itemset.split(" ");
            Set<String> conclusionComponent = new HashSet<String>(
                    Arrays.asList(itemsetComponent));
            conclusionComponent.removeAll(Arrays.asList(premisesComponent));
            if (conclusionComponent.size() == 1) {
                conclusionSupport = new Double(new Double(
                        freqItemMap.get(conclusionComponent.toArray()[0]))
                        / freqItemMap.get("dataset"));
            } else {
                conclusionSupport = -1.0;
            }
            ruleSupport = new Double((double) itemsetMap.get(itemset)
                    / freqItemMap.get("dataset"));
            confidence = new Double(ruleSupport / premisesSupport);
            lift = new Double(confidence / conclusionSupport);

            if (confidence.compareTo(minConfidence) >= 0) {
                context.write(new Text(key.toString()
                        + " => "
                        + conclusionComponent.toString().replace("[", "")
                                .replace("]", "").trim()),
                        new Text("(" + String.format("%.6f", ruleSupport)
                                + ", " + String.format("%.6f", confidence)
                                + ", " + String.format("%.6f", lift) + ")"));
            }
        }

    }

    @Override
    protected void setup(Context context) throws IOException,
            InterruptedException {
        super.setup(context);

        Parameters params = new Parameters(context.getConfiguration().get(
                "minConfidence", ""));

        /* Get Item Frequent List from DC */
        for (Pair<String, Long> e : ARM.readFList(context.getConfiguration())) {
            freqItemMap.put(e.getFirst(), e.getSecond());
        }

        minConfidence = Double.valueOf(params.get("minConfidence", "0.1"));
    }

}