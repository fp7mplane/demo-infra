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

package it.polito.dbdmg.searum.itemsets;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.mahout.common.Pair;
import org.apache.mahout.fpm.pfpgrowth.convertors.string.TopKStringPatterns;

/**
 * 
 * @author Luigi Grimaudo
 * @version 0.0.1 map each closed itemset with its complete set
 *
 */
public class ExpandClosedMapper extends
        Mapper<Text, TopKStringPatterns, Text, IntWritable> {

    @Override
    protected void map(Text key, TopKStringPatterns values, Context context)
            throws IOException, InterruptedException {
        /* loop for all the closed pattern containing the item key */
        for (Pair<List<String>, Long> pattern : values.getPatterns()) {

            List<String> strClosed = pattern.getFirst();
            Long support = pattern.getSecond();

            List<List<String>> ps = new ArrayList<List<String>>();
            ps.add(new ArrayList<String>());
            for (String item : strClosed) {
                List<List<String>> newPs = new ArrayList<List<String>>();
                for (List<String> subset : ps) {
                    newPs.add(subset);
                    List<String> newSubset = new ArrayList<String>(subset);
                    newSubset.add(item);
                    newPs.add(newSubset);
                    context.write(new Text(newSubset.toString()),
                            new IntWritable(support.intValue()));
                    ps = newPs;
                }
            }

        }
    }
}