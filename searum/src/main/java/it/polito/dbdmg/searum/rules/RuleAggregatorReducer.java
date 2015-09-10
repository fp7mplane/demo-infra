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

import java.io.IOException;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Reducer;

/**
 * 
 * @author Luigi Grimaudo
 * @version 0.0.1 reduce all the rules containing the key item.
 * 
 */
public class RuleAggregatorReducer extends Reducer<Text, Text, Text, Text> {

    @Override
    protected void reduce(Text key, Iterable<Text> values, Context context)
            throws IOException, InterruptedException {
        for (Text value : values) {
            String rule = value.toString().split("\t")[0];
            String[] measures = value.toString().split("\t")[1]
                    .replace("(", "").replace(")", "").split(",");
            Double support = new Double((new Double(measures[0])) * 100);
            Double confidence = new Double((new Double(measures[1])) * 100);
            Double lift = new Double((new Double(measures[2])));

            context.write(new Text(key.toString().split("#")[0]),
                    new Text(rule + "\t" + "(" + String.format("%.3f", support)
                            + "%, " + String.format("%.0f", confidence) + "%, "
                            + String.format("%.3f", lift) + ")"));
        }
    }
}