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

package it.polito.dbdmg.searum;

import it.polito.dbdmg.searum.discretization.DiscretizationMapper;
import it.polito.dbdmg.searum.itemsets.ExpandClosedMapper;
import it.polito.dbdmg.searum.itemsets.ExpandClosedReducer;
import it.polito.dbdmg.searum.itemsets.ParallelFPGrowthCombiner;
import it.polito.dbdmg.searum.itemsets.ParallelFPGrowthMapper;
import it.polito.dbdmg.searum.itemsets.ParallelFPGrowthReducer;
import it.polito.dbdmg.searum.itemsets.sorting.ClosedSortingMapper;
import it.polito.dbdmg.searum.itemsets.sorting.ClosedSortingReducer;
import it.polito.dbdmg.searum.itemsets.sorting.ItemsetSortingMapper;
import it.polito.dbdmg.searum.itemsets.sorting.ItemsetSortingReducer;
import it.polito.dbdmg.searum.rules.RuleAggregatorMapper;
import it.polito.dbdmg.searum.rules.RuleAggregatorReducer;
import it.polito.dbdmg.searum.rules.RuleMiningMapper;
import it.polito.dbdmg.searum.rules.RuleMiningReducer;
import it.polito.dbdmg.searum.rules.RulePartitionerByConclusion;
import it.polito.dbdmg.searum.rules.RulesGroupingWritableComparator;
import it.polito.dbdmg.searum.rules.RulesWritableComparator;
import it.polito.dbdmg.searum.utils.ParallelCountingMapper;
import it.polito.dbdmg.searum.utils.ParallelCountingReducer;

import java.io.IOException;
import java.net.URI;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.PriorityQueue;
import java.util.regex.Pattern;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.filecache.DistributedCache;
import org.apache.hadoop.fs.FileStatus;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.io.SequenceFile;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.input.SequenceFileInputFormat;
import org.apache.hadoop.mapreduce.lib.input.TextInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.mapreduce.lib.output.SequenceFileOutputFormat;
import org.apache.mahout.common.HadoopUtil;
import org.apache.mahout.common.Pair;
import org.apache.mahout.common.Parameters;
import org.apache.mahout.common.iterator.sequencefile.PathType;
import org.apache.mahout.common.iterator.sequencefile.SequenceFileDirIterable;
import org.apache.mahout.common.iterator.sequencefile.SequenceFileIterable;
import org.apache.mahout.fpm.pfpgrowth.TransactionTree;
import org.apache.mahout.fpm.pfpgrowth.convertors.string.TopKStringPatterns;
import org.apache.mahout.fpm.pfpgrowth.fpgrowth.FPGrowth;
import org.apache.mahout.math.list.IntArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.common.collect.Lists;

/**
 * 
 * Parallel FP Growth and Association Rule mining driver class. Runs each stage
 * of PFPGrowth as described in the paper
 * http://infolab.stanford.edu/~echang/recsys08-69.pdf Modified and integrated
 * for SEARUM as described in the paper
 * http://www.ict-mplane.eu/sites/default/files
 * //public/publications/386ispa2013grimaudo.pdf
 * 
 */
public final class ARM {

    public static final String ENCODING = "encoding";
    public static final String HEADER_TABLE = "header_table";
    public static final String G_LIST = "gList";
    public static final String NUM_GROUPS = "numGroups";
    public static final int NUM_GROUPS_DEFAULT = 1000;
    public static final String MAX_PER_GROUP = "maxPerGroup";
    public static final String OUTPUT = "output";
    public static final String MIN_SUPPORT = "minSupport";
    public static final String MAX_HEAPSIZE = "maxHeapSize";
    public static final String INPUT = "input";
    public static final String PFP_PARAMETERS = "pfp.parameters";
    public static final String FILE_PATTERN = "part-*";
    public static final String DISC = "discretized";
    public static final String FPGROWTH = "closed";
    public static final String FREQUENT_PATTERNS = "closed";
    public static final String ITEM_FREQ = "item_frequency";
    public static final String ITEMSETS = "itemsets";
    public static final String ITEMSETSORTED = "itemset_sorted";
    public static final String CLOSEDSORTED = "closed_sorted";
    public static final String RULES = "rules";
    public static final String RULESBYCONCLUSION = "rules_aggregated";
    public static final String SPLIT_PATTERN = "splitPattern";
    public static final String USE_FPG2 = "use_fpg2";
    public static final String JOBS = "jobs";
    public static final String ENABLE_DISCRETIZATION = "enableDiscretization";
    public static final String ENABLE_RULES = "enableRules";
    public static final String INPUT_TYPE = "type";
    public static final String TOOL = "SEARUM";
    public static final Pattern SPLITTER = Pattern
            .compile("[ ,\t]*[,|\t][ ,\t]*");
    private static final Logger log = LoggerFactory.getLogger(ARM.class);
    public static int absSupport;

    /**
     * Execute the chain of MapReduce jobs.
     * 
     * @param params
     *            params contains input and output locations as a string value,
     *            the additional parameters include discretize flag, minSupport
     *            and minConfidence
     */
    public static void runPFPGrowth(Parameters params) throws IOException,
            InterruptedException, ClassNotFoundException {
        Configuration conf = new Configuration();
        conf.set(
                "io.serializations",
                "org.apache.hadoop.io.serializer.JavaSerialization,"
                        + "org.apache.hadoop.io.serializer.WritableSerialization");
        Integer enableDiscretization = new Integer(
                params.get(ENABLE_DISCRETIZATION));
        Integer enableRules = new Integer(params.get(ENABLE_RULES));

        if (enableDiscretization.compareTo(new Integer(1)) == 0) {
            startDiscretization(params, conf);
        }

        startParallelCounting(params, conf);
        List<Pair<String, Long>> headerTable = readFList(params);
        saveFList(headerTable, params, conf);

        int numGroups = params.getInt(NUM_GROUPS, NUM_GROUPS_DEFAULT);
        int maxPerGroup = headerTable.size() / numGroups;
        if (headerTable.size() % numGroups != 0) {
            maxPerGroup++;
        }
        params.set(MAX_PER_GROUP, Integer.toString(maxPerGroup));

        startParallelFPGrowth(params, conf);
        startClosedSorting(params, conf);
        startExpandClosed(params, conf);
        startItemsetSorting(params, conf);

        if (enableRules.compareTo(new Integer(1)) == 0) {
            startRuleMining(params, conf);
            startRuleAggregating(params, conf);
        }
    }

    /**
     * Run discretization over input dataset.
     * 
     * @param params
     * @param conf
     */
    public static void startDiscretization(Parameters params, Configuration conf)
            throws IOException, ClassNotFoundException, InterruptedException {
        conf.set("mapred.compress.map.output", "true");
        conf.set("mapred.output.compression.type", "BLOCK");

        Path input = new Path(params.get(INPUT));
        Job job = new Job(conf, TOOL + "Discretization driver over input: "
                + input);
        job.setJarByClass(ARM.class);
        FileInputFormat.addInputPath(job, input);
        Path outPath = new Path(params.get(OUTPUT), DISC);
        FileOutputFormat.setOutputPath(job, outPath);

        job.setInputFormatClass(TextInputFormat.class);

        job.setMapOutputKeyClass(Text.class);
        job.setMapOutputValueClass(NullWritable.class);

        job.setNumReduceTasks(0);
        job.setMapperClass(DiscretizationMapper.class);

        HadoopUtil.delete(conf, outPath);
        boolean succeeded = job.waitForCompletion(true);
        if (!succeeded) {
            throw new IllegalStateException("Job failed!");
        }

    }

    /**
     * 
     * Count the frequencies of items
     * 
     * @param params
     * @param conf
     */
    public static void startParallelCounting(Parameters params,
            Configuration conf) throws IOException, InterruptedException,
            ClassNotFoundException {
        conf.set(PFP_PARAMETERS, params.toString());

        conf.set("mapred.compress.map.output", "true");
        conf.set("mapred.output.compression.type", "BLOCK");

        Path input;
        Integer enableDiscretization = new Integer(
                params.get(ENABLE_DISCRETIZATION));
        if (enableDiscretization.compareTo(new Integer(1)) == 0) {
            input = new Path(params.get(OUTPUT), DISC);
        } else {
            input = new Path(params.get(INPUT));
        }

        Job job = new Job(conf, "Parallel Counting driver running over input: "
                + input);
        job.setJarByClass(ARM.class);

        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(LongWritable.class);

        FileInputFormat.addInputPath(job, input);
        Path outPath = new Path(params.get(OUTPUT), ITEM_FREQ);
        FileOutputFormat.setOutputPath(job, outPath);

        HadoopUtil.delete(conf, outPath);

        job.setInputFormatClass(TextInputFormat.class);
        job.setMapperClass(ParallelCountingMapper.class);
        job.setCombinerClass(ParallelCountingReducer.class);
        job.setReducerClass(ParallelCountingReducer.class);
        job.setOutputFormatClass(SequenceFileOutputFormat.class);

        boolean succeeded = job.waitForCompletion(true);
        if (!succeeded) {
            throw new IllegalStateException("Job failed!");
        }

    }

    /**
     * Read the header table which is built at the end of the Parallel counting
     * job.
     * 
     * @return header table
     */
    public static List<Pair<String, Long>> readFList(Parameters params) {
        Configuration conf = new Configuration();

        Path parallelCountingPath = new Path(params.get(OUTPUT), ITEM_FREQ);

        PriorityQueue<Pair<String, Long>> queue = new PriorityQueue<Pair<String, Long>>(
                11, new Comparator<Pair<String, Long>>() {

                    public int compare(Pair<String, Long> o1,
                            Pair<String, Long> o2) {
                        int ret = o2.getSecond().compareTo(o1.getSecond());
                        if (ret != 0) {
                            return ret;
                        }
                        return o1.getFirst().compareTo(o2.getFirst());
                    }
                });

        /**
         * Get absolute support from relative threshold
         */
        Long numTrans = null;

        for (Pair<Text, LongWritable> record : new SequenceFileDirIterable<Text, LongWritable>(
                new Path(parallelCountingPath, FILE_PATTERN), PathType.GLOB,
                null, null, true, conf)) {
            long value = record.getSecond().get();
            String feature = record.getFirst().toString();
            if (feature.compareTo("dataset") == 0) {
                numTrans = value;
                break;
            }

        }

        Double relativeSupport = Double.valueOf(params.get(MIN_SUPPORT, "0.9"));
        absSupport = (int) Math.ceil((relativeSupport * numTrans));

        log.info("# Transactions: " + numTrans);
        log.info("Support: " + relativeSupport * 100 + "%");
        log.info("Support count: " + absSupport);
        params.set(MIN_SUPPORT, (new Long(absSupport)).toString());

        for (Pair<Text, LongWritable> record : new SequenceFileDirIterable<Text, LongWritable>(
                new Path(parallelCountingPath, FILE_PATTERN), PathType.GLOB,
                null, null, true, conf)) {
            long value = record.getSecond().get();
            if (value >= absSupport) {
                queue.add(new Pair<String, Long>(record.getFirst().toString(),
                        value));
            }
        }

        List<Pair<String, Long>> fList = Lists.newArrayList();
        while (!queue.isEmpty()) {
            fList.add(queue.poll());
        }
        return fList;
    }

    /**
     * Serializes the header table and returns the string representation of the
     * header table
     * 
     * @return Serialized String representation of header table
     */
    public static void saveFList(Iterable<Pair<String, Long>> flist,
            Parameters params, Configuration conf) throws IOException {
        Path flistPath = new Path(params.get(OUTPUT), HEADER_TABLE);
        FileSystem fs = FileSystem.get(flistPath.toUri(), conf);
        flistPath = fs.makeQualified(flistPath);
        HadoopUtil.delete(conf, flistPath);
        SequenceFile.Writer writer = new SequenceFile.Writer(fs, conf,
                flistPath, Text.class, LongWritable.class);
        try {
            for (Pair<String, Long> pair : flist) {
                writer.append(new Text(pair.getFirst()),
                        new LongWritable(pair.getSecond()));
            }
        } finally {
            writer.close();
        }
        DistributedCache.addCacheFile(flistPath.toUri(), conf);
    }

    public static int getGroup(int itemId, int maxPerGroup) {
        return itemId / maxPerGroup;
    }

    public static IntArrayList getGroupMembers(int groupId, int maxPerGroup,
            int numFeatures) {
        IntArrayList ret = new IntArrayList();
        int start = groupId * maxPerGroup;
        int end = start + maxPerGroup;
        if (end > numFeatures) {
            end = numFeatures;
        }
        for (int i = start; i < end; i++) {
            ret.add(i);
        }
        return ret;
    }

    /**
     * Generates the header table from the serialized string representation
     * 
     * @return Deserialized header table
     */
    public static List<Pair<String, Long>> readFList(Configuration conf)
            throws IOException {
        List<Pair<String, Long>> list = new ArrayList<Pair<String, Long>>();
        Path[] files = DistributedCache.getLocalCacheFiles(conf);
        if (files == null) {
            throw new IOException(
                    "Cannot read Frequency list from Distributed Cache");
        }
        if (files.length != 1) {
            throw new IOException(
                    "Cannot read Frequency list from Distributed Cache ("
                            + files.length + ')');
        }
        FileSystem fs = FileSystem.getLocal(conf);
        Path fListLocalPath = fs.makeQualified(files[0]);
        // Fallback if we are running locally.
        if (!fs.exists(fListLocalPath)) {
            URI[] filesURIs = DistributedCache.getCacheFiles(conf);
            if (filesURIs == null) {
                throw new IOException(
                        "Cannot read header table from Distributed Cache");
            }
            if (filesURIs.length != 1) {
                throw new IOException(
                        "Cannot read header table from Distributed Cache ("
                                + files.length + ')');
            }
            fListLocalPath = new Path(filesURIs[0].getPath());
        }
        for (Pair<Text, LongWritable> record : new SequenceFileIterable<Text, LongWritable>(
                fListLocalPath, true, conf)) {
            list.add(new Pair<String, Long>(record.getFirst().toString(),
                    record.getSecond().get()));
        }
        return list;
    }

    /**
     * 
     * @return List of TopK patterns for each string frequent feature
     */
    public static List<Pair<String, TopKStringPatterns>> readFrequentPattern(
            Parameters params) throws IOException {

        Configuration conf = new Configuration();

        Path frequentPatternsPath = new Path(params.get(OUTPUT),
                FREQUENT_PATTERNS);
        FileSystem fs = FileSystem.get(frequentPatternsPath.toUri(), conf);
        FileStatus[] outputFiles = fs.globStatus(new Path(frequentPatternsPath,
                FILE_PATTERN));

        List<Pair<String, TopKStringPatterns>> ret = Lists.newArrayList();
        for (FileStatus fileStatus : outputFiles) {
            ret.addAll(FPGrowth.readFrequentPattern(conf, fileStatus.getPath()));
        }
        return ret;
    }

    /**
     * Run the Parallel FPGrowth Map/Reduce job to calculate the Top K features
     * of group dependent shards
     */
    public static void startParallelFPGrowth(Parameters params,
            Configuration conf) throws IOException, InterruptedException,
            ClassNotFoundException {
        conf.set(PFP_PARAMETERS, params.toString());
        conf.set("mapred.compress.map.output", "true");
        conf.set("mapred.output.compression.type", "BLOCK");
        Path input;
        Integer enableDiscretization = new Integer(
                params.get(ENABLE_DISCRETIZATION));
        if (enableDiscretization.compareTo(new Integer(1)) == 0) {
            input = new Path(params.get(OUTPUT), DISC);
        } else {
            input = new Path(params.get(INPUT));
        }
        Job job = new Job(conf, "PFP Growth driver running over input" + input);
        job.setJarByClass(ARM.class);

        job.setMapOutputKeyClass(IntWritable.class);
        job.setMapOutputValueClass(TransactionTree.class);

        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(TopKStringPatterns.class);

        FileInputFormat.addInputPath(job, input);
        Path outPath = new Path(params.get(OUTPUT), FPGROWTH);
        FileOutputFormat.setOutputPath(job, outPath);

        HadoopUtil.delete(conf, outPath);

        job.setInputFormatClass(TextInputFormat.class);
        job.setMapperClass(ParallelFPGrowthMapper.class);
        job.setCombinerClass(ParallelFPGrowthCombiner.class);
        job.setReducerClass(ParallelFPGrowthReducer.class);
        job.setOutputFormatClass(SequenceFileOutputFormat.class);

        boolean succeeded = job.waitForCompletion(true);
        if (!succeeded) {
            throw new IllegalStateException("Job failed!");
        }
    }

    /**
     * Sort frequent closed itemsets by support
     * 
     * @param params
     * @param conf
     * @throws IOException
     * @throws ClassNotFoundException
     * @throws InterruptedException
     */
    public static void startClosedSorting(Parameters params, Configuration conf)
            throws IOException, ClassNotFoundException, InterruptedException {
        conf.set("mapred.compress.map.output", "true");
        conf.set("mapred.output.compression.type", "BLOCK");

        Path input = new Path(params.get(OUTPUT), FPGROWTH);
        Job job = new Job(conf, "Closed sorting driver running over input: "
                + input);
        job.setJarByClass(ARM.class);
        FileInputFormat.addInputPath(job, input);
        Path outPath = new Path(params.get(OUTPUT), CLOSEDSORTED);
        FileOutputFormat.setOutputPath(job, outPath);

        job.setInputFormatClass(SequenceFileInputFormat.class);

        job.setMapOutputKeyClass(LongWritable.class);
        job.setMapOutputValueClass(Text.class);

        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(Text.class);

        job.setMapperClass(ClosedSortingMapper.class);
        job.setReducerClass(ClosedSortingReducer.class);

        job.setNumReduceTasks(1);

        HadoopUtil.delete(conf, outPath);
        boolean succeeded = job.waitForCompletion(true);
        if (!succeeded) {
            throw new IllegalStateException("Job failed!");
        }
    }

    /**
     * Run the expansion job to extract itemset from closed patterns
     * 
     * @param params
     * @param conf
     * @throws IOException
     * @throws InterruptedException
     * @throws ClassNotFoundException
     */
    public static void startExpandClosed(Parameters params, Configuration conf)
            throws IOException, InterruptedException, ClassNotFoundException {
        conf.set("mapred.compress.map.output", "true");
        conf.set("mapred.output.compression.type", "BLOCK");

        Path input = new Path(params.get(OUTPUT), FPGROWTH);
        Job job = new Job(conf, "Itemset expansion driver running over input: "
                + input);
        job.setJarByClass(ARM.class);

        FileInputFormat.addInputPath(job, input);
        Path outPath = new Path(params.get(OUTPUT), ITEMSETS);
        FileOutputFormat.setOutputPath(job, outPath);

        job.setInputFormatClass(SequenceFileInputFormat.class);

        job.setMapOutputKeyClass(Text.class);
        job.setMapOutputValueClass(IntWritable.class);

        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(IntWritable.class);

        job.setMapperClass(ExpandClosedMapper.class);
        job.setReducerClass(ExpandClosedReducer.class);

        HadoopUtil.delete(conf, outPath);
        boolean succeeded = job.waitForCompletion(true);
        if (!succeeded) {
            throw new IllegalStateException("Job failed!");
        }
    }

    /**
     * Sort frequent itemsets by support.
     * 
     * @param params
     * @param conf
     * @throws IOException
     * @throws ClassNotFoundException
     * @throws InterruptedException
     */
    public static void startItemsetSorting(Parameters params, Configuration conf)
            throws IOException, ClassNotFoundException, InterruptedException {
        conf.set("mapred.compress.map.output", "true");
        conf.set("mapred.output.compression.type", "BLOCK");

        Path input = new Path(params.get(OUTPUT), ITEMSETS);
        Job job = new Job(conf, "Itemset sorting driver running over input: "
                + input);
        job.setJarByClass(ARM.class);
        FileInputFormat.addInputPath(job, input);
        Path outPath = new Path(params.get(OUTPUT), ITEMSETSORTED);
        FileOutputFormat.setOutputPath(job, outPath);

        job.setMapOutputKeyClass(LongWritable.class);
        job.setMapOutputValueClass(Text.class);

        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(Text.class);

        job.setMapperClass(ItemsetSortingMapper.class);
        job.setReducerClass(ItemsetSortingReducer.class);

        job.setNumReduceTasks(1);

        HadoopUtil.delete(conf, outPath);
        boolean succeeded = job.waitForCompletion(true);
        if (!succeeded) {
            throw new IllegalStateException("Job failed!");
        }
    }

    /**
     * Run the rule mining job from the itemset extracted during previous job
     * 
     * @param params
     * @param conf
     * @throws IOException
     * @throws InterruptedException
     * @throws ClassNotFoundException
     */
    public static void startRuleMining(Parameters params, Configuration conf)
            throws IOException, InterruptedException, ClassNotFoundException {
        conf.set("minConfidence", params.toString());
        conf.set("mapred.compress.map.output", "true");
        conf.set("mapred.output.compression.type", "BLOCK");

        Path input = new Path(params.get(OUTPUT), ITEMSETS);
        Job job = new Job(conf, "PFP Rule Mining driver running over input: "
                + input);
        job.setJarByClass(ARM.class);
        FileInputFormat.addInputPath(job, input);
        Path outPath = new Path(params.get(OUTPUT), RULES);
        FileOutputFormat.setOutputPath(job, outPath);

        job.setMapOutputKeyClass(Text.class);
        job.setMapOutputValueClass(Text.class);

        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(Text.class);

        job.setMapperClass(RuleMiningMapper.class);
        job.setReducerClass(RuleMiningReducer.class);

        HadoopUtil.delete(conf, outPath);
        boolean succeeded = job.waitForCompletion(true);
        if (!succeeded) {
            throw new IllegalStateException("Job failed!");
        }
    }

    /**
     * Run the rule aggregator job over mined rules.
     * 
     * @throws IOException
     * @throws InterruptedException
     * @throws ClassNotFoundException
     */
    public static void startRuleAggregating(Parameters params,
            Configuration conf) throws IOException, ClassNotFoundException,
            InterruptedException {
        conf.set("mapred.compress.map.output", "true");
        conf.set("mapred.output.compression.type", "BLOCK");

        Path input = new Path(params.get(OUTPUT), RULES);
        Job job = new Job(conf, "Rule aggregator driver running over input: "
                + input);
        job.setJarByClass(ARM.class);
        FileInputFormat.addInputPath(job, input);
        Path outPath = new Path(params.get(OUTPUT), RULESBYCONCLUSION);
        FileOutputFormat.setOutputPath(job, outPath);

        job.setMapOutputKeyClass(Text.class);
        job.setMapOutputValueClass(Text.class);

        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(Text.class);

        job.setMapperClass(RuleAggregatorMapper.class);
        job.setReducerClass(RuleAggregatorReducer.class);
        job.setPartitionerClass(RulePartitionerByConclusion.class);
        job.setSortComparatorClass(RulesWritableComparator.class);
        job.setGroupingComparatorClass(RulesGroupingWritableComparator.class);

        HadoopUtil.delete(conf, outPath);
        boolean succeeded = job.waitForCompletion(true);
        if (!succeeded) {
            throw new IllegalStateException("Job failed!");
        }
    }
}
