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

import it.polito.dbdmg.searum.ARM;
import it.polito.dbdmg.searum.utils.CountDescendingPairComparator;

import java.io.IOException;
import java.util.Collections;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map.Entry;

import org.apache.commons.lang.mutable.MutableLong;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.mahout.common.Pair;
import org.apache.mahout.common.Parameters;
import org.apache.mahout.fpm.pfpgrowth.TransactionTree;
import org.apache.mahout.fpm.pfpgrowth.convertors.ContextStatusUpdater;
import org.apache.mahout.fpm.pfpgrowth.convertors.ContextWriteOutputCollector;
import org.apache.mahout.fpm.pfpgrowth.convertors.integer.IntegerStringOutputConverter;
import org.apache.mahout.fpm.pfpgrowth.convertors.string.TopKStringPatterns;
import org.apache.mahout.fpm.pfpgrowth.fpgrowth.FPGrowth;
import org.apache.mahout.math.list.IntArrayList;
import org.apache.mahout.math.list.LongArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.common.collect.Lists;

/**
 * takes each group of transactions and runs vanilla FPGrowth on it and outputs
 * the the Top K frequent Patterns for each group.
 * 
 */
public final class ParallelFPGrowthReducer extends
        Reducer<IntWritable, TransactionTree, Text, TopKStringPatterns> {

    private final List<String> featureReverseMap = Lists.newArrayList();
    private final LongArrayList freqList = new LongArrayList();
    private int maxHeapSize;
    private int minSupport;
    private int numFeatures;
    private int maxPerGroup;

    private static final Logger log = LoggerFactory
            .getLogger(ParallelFPGrowthReducer.class);

    private static class IteratorAdapter implements
            Iterator<Pair<List<Integer>, Long>> {
        private final Iterator<Pair<IntArrayList, Long>> innerIter;

        private IteratorAdapter(
                Iterator<Pair<IntArrayList, Long>> transactionIter) {
            innerIter = transactionIter;
        }

        public boolean hasNext() {
            return innerIter.hasNext();
        }

        public Pair<List<Integer>, Long> next() {
            Pair<IntArrayList, Long> innerNext = innerIter.next();
            return new Pair<List<Integer>, Long>(innerNext.getFirst().toList(),
                    innerNext.getSecond());
        }

        public void remove() {
            throw new UnsupportedOperationException();
        }
    }

    @Override
    protected void reduce(IntWritable key, Iterable<TransactionTree> values,
            Context context) throws IOException {
        TransactionTree cTree = new TransactionTree();
        for (TransactionTree tr : values) {
            for (Pair<IntArrayList, Long> p : tr) {
                cTree.addPattern(p.getFirst(), p.getSecond());
            }
        }

        List<Pair<Integer, Long>> localFList = Lists.newArrayList();
        for (Entry<Integer, org.apache.commons.lang3.mutable.MutableLong> fItem : cTree
                .generateFList().entrySet()) {
            localFList.add(new Pair<Integer, Long>(fItem.getKey(), fItem
                    .getValue().toLong()));
        }

        Collections.sort(localFList,
                new CountDescendingPairComparator<Integer, Long>());

        FPGrowth<Integer> fpGrowth = new FPGrowth<Integer>();
        fpGrowth.generateTopKFrequentPatterns(
                new IteratorAdapter(cTree.iterator()),
                localFList,
                minSupport,
                maxHeapSize,
                new HashSet<Integer>(ARM.getGroupMembers(key.get(),
                        maxPerGroup, numFeatures).toList()),
                new IntegerStringOutputConverter(
                        new ContextWriteOutputCollector<IntWritable, TransactionTree, Text, TopKStringPatterns>(
                                context), featureReverseMap),
                new ContextStatusUpdater<IntWritable, TransactionTree, Text, TopKStringPatterns>(
                        context));
    }

    @Override
    protected void setup(Context context) throws IOException,
            InterruptedException {

        super.setup(context);
        Parameters params = new Parameters(context.getConfiguration().get(
                ARM.PFP_PARAMETERS, ""));

        for (Pair<String, Long> e : ARM.readFList(context.getConfiguration())) {
            if (!e.equals("dataset")) {
                featureReverseMap.add(e.getFirst());
                freqList.add(e.getSecond());
            }
        }

        maxHeapSize = Integer.valueOf(params.get(ARM.MAX_HEAPSIZE, "50"));
        minSupport = Integer.valueOf(params.get(ARM.MIN_SUPPORT, "5"));
        log.info("Support count: " + minSupport);
        maxPerGroup = params.getInt(ARM.MAX_PER_GROUP, 0);
        numFeatures = featureReverseMap.size();
    }
}
