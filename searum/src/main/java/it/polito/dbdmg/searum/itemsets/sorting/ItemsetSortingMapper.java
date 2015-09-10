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

package it.polito.dbdmg.searum.itemsets.sorting;

import it.polito.dbdmg.searum.ARM;

import java.io.IOException;

import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.mahout.common.Pair;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * @author Luigi Grimaudo
 * @version 0.1
 * 
 *          sorting mapper
 * 
 */
public class ItemsetSortingMapper extends
        Mapper<LongWritable, Text, LongWritable, Text> {

    private Long trans;
    private static final Logger log = LoggerFactory
            .getLogger(ItemsetSortingMapper.class);

    @Override
    protected void map(LongWritable key, Text value, Context context)
            throws IOException, InterruptedException {

        String realKey = value.toString().split("\t")[0];
        String realValue = value.toString().split("\t")[1];

        Long support = new Long(realValue);

        context.write(
                new LongWritable(-support),
                new Text(realKey
                        + "\t"
                        + support
                        + " - "
                        + String.format("%.3f",
                                (((double) support) / trans * 100)) + "%"));

    }

    @Override
    protected void setup(Context context) throws IOException,
            InterruptedException {
        super.setup(context);
        for (Pair<String, Long> e : ARM.readFList(context.getConfiguration())) {
            if (e.getFirst().compareTo("dataset") == 0) {
                trans = e.getSecond();
                break;
            }

        }
    }
}
