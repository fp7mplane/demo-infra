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
import java.util.ArrayList;

import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;

/**
 * 
 * @author Luigi Grimaudo
 * @version 0.0.1 map each itemset with the itemset itself and all the
 *          sub-itemset from the conditional pattern base of a single item
 *
 */
public class RuleMiningMapper extends Mapper<LongWritable, Text, Text, Text> {

    @Override
    protected void map(LongWritable key, Text value, Context context)
            throws IOException, InterruptedException {

        // A <k,v> pair is <itemset, support>
        // Example <[a, b, c]; 2>
        // Emit: <a, b, c; 2>
        // <a, b; a, b, c - 2>

        String realKey = value.toString().split("\t")[0];
        String realValue = value.toString().split("\t")[1];
        String tempItemset = realKey.toString();
        String itemset = tempItemset.replace("[", "").replace("]", "");
        String[] items = itemset.split(",");
        String itemsetBaseString = itemset.replace(", ", " ").trim();

        context.write(new Text(itemsetBaseString),
                new Text(realValue.toString()));
        if (items.length > 1) {
            for (String currBaseItem : items) {
                currBaseItem = currBaseItem.trim();
                StringBuilder condPatternBuilder = new StringBuilder();
                for (String item : items) {
                    item = item.trim();
                    if (!item.equals(currBaseItem)) {
                        condPatternBuilder.append(item + " ");
                    }
                }
                String condPatternString = condPatternBuilder.toString().trim();
                context.write(new Text(condPatternString), new Text(
                        itemsetBaseString + "," + realValue.toString()));
            }
        }
    }
}
