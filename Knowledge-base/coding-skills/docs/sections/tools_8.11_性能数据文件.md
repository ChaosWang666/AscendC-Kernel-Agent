<!-- Source: 算子开发工具.md lines 9431-9756 | Section: 8.11 性能数据文件 -->

# 8.11 性能数据文件

# 8.11.1 msprof op

# 8.11.1.1 ArithmeticUtilization（cube 及 vector 类型指令耗时和占比）

cube及vector类型指令的cycle占比数据ArithmeticUtilization.csv，建议优化算子逻 辑，减少冗余计算指令。详情介绍请参见下表中的字段说明。 

# Atlas A3 训练系列产品/Atlas A3 推理系列产品及 Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件


图 8-12 ArithmeticUtilization.csv 文件


<table><tr><td>block_id</td><td>sub_block_id</td><td>aic_time(us)</td><td>aic_total_c_yales</td><td>aic_cube_intp16_ratio</td><td>aic_cube_int8_ratio</td><td>aic_cube_fops</td><td>aic_cube_t0atal_instnum_number</td><td>aic_cube_t0int_instrnum_number</td><td>aiv_time(us)</td><td>aiv_total_c_yales</td><td>aiv_vec_ratioc</td><td>aiv_vec_f032_ratio</td><td>aiv_vec_f016_ratio</td><td>aiv_vec_int32_ratio</td><td>aiv_vec_int16_ratio</td><td>aiv_vec_miscc_ratio</td><td>aiv_vec_misrc_ratio</td></tr><tr><td>0</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.092727</td><td>8403</td><td>0.075687</td><td>0</td><td>0.001904</td><td>0</td><td>0</td><td>0.008092</td><td>4224</td></tr><tr><td>1</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.172727</td><td>8535</td><td>0.074517</td><td>0</td><td>0.001875</td><td>0</td><td>0</td><td>0.007967</td><td>4224</td></tr><tr><td>2</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.271515</td><td>8698</td><td>0.07312</td><td>0</td><td>0.00184</td><td>0</td><td>0</td><td>0.007818</td><td>4224</td></tr><tr><td>3</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.093333</td><td>8404</td><td>0.074488</td><td>0</td><td>0.001904</td><td>0</td><td>0</td><td>0.008091</td><td>4224</td></tr><tr><td>4</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.141212</td><td>8483</td><td>0.074973</td><td>0</td><td>0.001886</td><td>0</td><td>0</td><td>0.008016</td><td>4224</td></tr><tr><td>5</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.299394</td><td>8744</td><td>0.073879</td><td>0</td><td>0.00183</td><td>0</td><td>0</td><td>0.007777</td><td>4224</td></tr><tr><td>6</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.161212</td><td>8516</td><td>0.073509</td><td>0</td><td>0.001879</td><td>0</td><td>0</td><td>0.007985</td><td>4224</td></tr><tr><td>7</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.240606</td><td>8647</td><td>0.074708</td><td>0</td><td>0.00185</td><td>0</td><td>0</td><td>0.007864</td><td>4224</td></tr></table>

关键字段说明如下。 


表 8-13 字段说明


<table><tr><td>字段名</td><td>字段解释</td></tr><tr><td>block_id</td><td>Task运行切分数量，对应Task运行时配置的核数。</td></tr><tr><td>sub_block_id</td><td>Block上Vector\Cube核的ID。</td></tr><tr><td>aic_time(us)</td><td>该Task被分配到每个AI Cube Core计算单元上后，每个AI Cube Core计算单元上的执行时间，单位us。</td></tr><tr><td>aic_total_cycles</td><td>该Task被分配到每个AI Cube Core计算单元上后，每个AI Cube Core计算单元上的执行的cycle总数。</td></tr><tr><td>aiv_time(us)</td><td>该Task被分配到每个AI Vector Core计算单元上后，每个AI Vector Core计算单元上的执行时间，单位us。</td></tr><tr><td>aiv_total_cycles</td><td>该Task被分配到每个AI Vector Core计算单元上后，每个AI Vector Core计算单元上的执行的cycle总数。</td></tr><tr><td>aic_cube_ratio</td><td>代表cube单元指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>aic_cube.fp16_rati0</td><td>代表cube fp16类型指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>aic_cube_int8_ratio</td><td>代表cube int8类型指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>aic_cube_fops</td><td>代表cube类型的浮点运算数，即计算量，可用于衡量算法/模型的复杂度，其中fops表示floating point operations。</td></tr><tr><td>aic Cube_total_inst_number</td><td>代表cube指令的总条数，包括fp和int类型。</td></tr><tr><td>aic_cube_fp_instr_nnumber</td><td>代表cube fp类型指令的总条数。</td></tr><tr><td>aic_cube_int_instr_number</td><td>代表cube int类型指令的总条数。</td></tr><tr><td>aiv_vec_ratio</td><td>代表vec单元指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>aiv_vec_fp32_ratio</td><td>代表vec fp32类型指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>aiv_vec_fp16_ratio</td><td>代表vec fp16类型指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>aiv_vec_int32_ratio</td><td>代表vec int32类型指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>aiv_vec_int16_ratio</td><td>代表vec int16类型指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>aiv_vec_misc_ratio</td><td>代表vec misc类型指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>aiv_vec_fops</td><td>代表vector类型浮点运算数，即计算量，可用于衡量算法/模型的复杂度，其中fops表示floating point operations。</td></tr></table>

# Atlas 推理系列产品


图 8-13 ArithmeticUtilization.csv 文件


<table><tr><td>aic_time(us)</td><td>aic_total_cycles</td><td>aic_cube_ratio</td><td>aic Cube, fp16 ratio</td><td>aic Cube,int8 ratio</td><td>aic Cube_fops</td><td>aic Cube_total_inst_number</td><td>aic_vec_ratio</td><td>aic_vec_f32_ratio</td><td>aic_vec_f16_ratio</td><td>aic_vec_int32_ratio</td><td>aic_vec_int16_ratio</td><td>aic_vec_misc_ratio</td><td>aic_vec_fops</td></tr><tr><td>4.322174</td><td>39764</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0.194749</td><td>0</td><td>0.103008</td><td>0</td><td>0</td><td>0</td><td>524288</td></tr></table>

关键字段说明如下。 


表8-14 字段说明


<table><tr><td>字段名</td><td>字段解释</td></tr><tr><td>aic_time(us)</td><td>该Task被分配到每个AI Core计算单元上后，每个AI Core计算单元上的执行时间，单位us。</td></tr><tr><td>aic_total_cycles</td><td>该Task被分配到每个AI Core计算单元上后，每个AI Core计算单元上的执行的cycle总数。</td></tr><tr><td>aic_cube_ratio</td><td>代表cube单元指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>aic_cube.fp16_rati0</td><td>代表cube fp16类型指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>aic_cube_int8_ratio</td><td>代表cube int8类型指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>aic_cube_fops</td><td>代表cube类型的浮点运算数，即计算量，可用于衡量算法/模型的复杂度，其中fops表示floating point operations。</td></tr><tr><td>aic_cube_total_inst_number</td><td>代表cube指令的总条数，包括fp和int类型。</td></tr><tr><td>aic_vec_ratio</td><td>代表vec单元指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>aic_vec.fp32_ratio</td><td>代表vec fp32类型指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>aic_vec.fp16_ratio</td><td>代表vec fp16类型指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>aic_vec_int32_ratio</td><td>代表vec int32类型指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>aic_vec_int16_ratio</td><td>代表vec int16类型指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>aic_vec_misc_ratio</td><td>代表vec misc类型指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>aic_vec_fops</td><td>代表vector类型浮点运算数，即计算量，可用于衡量算法/模型的复杂度，其中fops表示floating point operations。</td></tr></table>

# 8.11.1.2 L2Cache（L2 Cache 命中率）

L2 Cache命中率数据L2Cache.csv，影响MTE2（Memory Transfer Engine，数据搬入 单元），建议合理规划数据搬运逻辑，增加命中率。详情介绍请参见下表中的字段说 明。 

# Atlas A3 训练系列产品/Atlas A3 推理系列产品及 Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件


图 8-14 L2Cache.csv 文件


<table><tr><td>block_id</td><td>sub_block_jid</td><td>ac_time(u)</td><td>ac_total_c</td><td>acy_cycle</td><td>ac_write_cache_hit</td><td>ac_write_cache_miss_allocate</td><td>ac_r0_rea_dcache_hit</td><td>ac_r0_rea_dcache_hit</td><td>ac_r1_rea_dcache_hit</td><td>ac_r1_rea_dcache_hit</td><td>ac_r1_rea_dcache_hit</td><td>ac_write_hit_rate(%)</td><td>ac_total_c</td><td>acy_time(u)</td><td>ac_total_c</td><td>acy_cycle</td><td>ac_write_cache_hit</td><td>ac_write_cache_miss_allocate</td><td>ac_r0_rea_dcache_hit</td><td>ac_r0_rea_dcache_hit</td><td>ac_r1_rea_dcache_hit</td><td>ac_r1_rea_dcache_hit</td><td>ac_write_hit_rate(%)</td><td>ac_readHit rate(%)</td></tr><tr><td>0</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.092727</td><td>8403</td><td>20</td><td>8</td><td>32</td><td>19</td><td>28</td><td>18</td><td>71.42857</td><td>61.85567</td><td>64</td><td></td></tr><tr><td>1</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.172727</td><td>8535</td><td>20</td><td>8</td><td>27</td><td>17</td><td>33</td><td>20</td><td>71.42857</td><td>61.85567</td><td>64</td><td></td></tr><tr><td>2</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.271515</td><td>8698</td><td>20</td><td>8</td><td>30</td><td>18</td><td>29</td><td>20</td><td>71.42857</td><td>60.82474</td><td>63.2</td><td></td></tr><tr><td>3</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.093333</td><td>8404</td><td>20</td><td>8</td><td>32</td><td>18</td><td>28</td><td>19</td><td>71.42857</td><td>61.85567</td><td>64</td><td></td></tr><tr><td>4</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.412112</td><td>8403</td><td>20</td><td>8</td><td>31</td><td>18</td><td>29</td><td>19</td><td>71.42857</td><td>61.85567</td><td>64</td><td></td></tr><tr><td>5</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.299394</td><td>8744</td><td>20</td><td>8</td><td>30</td><td>19</td><td>30</td><td>18</td><td>71.42857</td><td>61.85567</td><td>64</td><td></td></tr><tr><td>6</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.161212</td><td>8516</td><td>20</td><td>8</td><td>29</td><td>18</td><td>31</td><td>19</td><td>71.42857</td><td>61.85567</td><td>64</td><td></td></tr><tr><td>7</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.240606</td><td>8647</td><td>20</td><td>8</td><td>31</td><td>19</td><td>29</td><td>18</td><td>71.42857</td><td>61.85567</td><td>64</td><td></td></tr></table>

关键字段说明如下。 


表 8-15 字段说明


<table><tr><td>字段名</td><td>字段解释</td></tr><tr><td>block_id</td><td>Task运行切分数量，对应Task运行时配置的核数。</td></tr><tr><td>sub_block_id</td><td>Task运行使用的每个block名称和序号。</td></tr><tr><td>aic_time(us)</td><td>该Task被分配到每个AI Cube Core计算单元上后，每个AI Cube Core计算单元上的执行时间，单位us。</td></tr><tr><td>aic_total_cycles</td><td>该Task被分配到每个AI Cube Core计算单元上后，每个AI Cube Core计算单元上的执行的cycle总数。</td></tr><tr><td>aiv_time(us)</td><td>该Task被分配到每个AI Vector Core计算单元上后，每个AI Vector Core计算单元上的执行时间，单位us。</td></tr><tr><td>aiv_total_cycles</td><td>该Task被分配到每个AI Vector Core计算单元上后，每个AI Vector Core计算单元上的执行的cycle总数。</td></tr><tr><td>ai*write_cache_hit</td><td>写cache命中的次数。</td></tr><tr><td>ai*write_cache_miss_allocate</td><td>写cache缺失后重新分配缓存的次数。</td></tr><tr><td>ai*r*_read_cache_hit</td><td>读r*通道cache命中次数。</td></tr><tr><td>ai*r*_read_cache_miss_allocate</td><td>读r*通道cache缺失后重新分配的次数。</td></tr><tr><td>ai*write_hit_rate(%)</td><td>写cache命中率。</td></tr><tr><td>ai*read_hit_rate(%)</td><td>读cache命中率。</td></tr><tr><td>ai*total_hit_rate(%)</td><td>读/写cache命中率。</td></tr></table>

# Atlas 推理系列产品


图 8-15 L2Cache.csv 文件


<table><tr><td>aic_l2_cache_hit_rate(%)</td></tr><tr><td>99.968201</td></tr></table>

关键字段说明如下。 


表8-16 字段说明


<table><tr><td>字段名</td><td>字段解释</td></tr><tr><td>aic_l2_cache_hit_rate</td><td>内存访问请求命中L2次数与总次数的比值。</td></tr></table>

# 8.11.1.3 Memory（内存读写带宽速率）

UB/L1/L2/主存储器采集内存读写带宽速率数据Memory.csv。详情介绍请参见下表中 的字段说明。 

# Atlas A3 训练系列产品/Atlas A3 推理系列产品及 Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件


图 8-16 Memory.csv 文件


<table><tr><td>bode</td><td>sub bode</td><td>ex bode</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex mea</td><td>ex meaa</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>1</td><td>VHEDO</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td></tr><tr><td>2</td><td>VHEDO</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td></tr><tr><td>3</td><td>VHEDO</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td></tr><tr><td>4</td><td>VHEDO</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td></tr><tr><td>5</td><td>VHEDO</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td></tr><tr><td>6</td><td>VHEDO</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td></tr><tr><td>7</td><td>VHEDO</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td></tr></table>

关键字段说明如下。 


表 8-17 字段说明


<table><tr><td>字段名</td><td>字段解释</td></tr><tr><td>block_id</td><td>Task运行切分数量，对应Task运行时配置的核数。</td></tr><tr><td>sub_block_id</td><td>Task运行使用的每个block名称和序号。</td></tr><tr><td>aic_time(us)</td><td>该Task被分配到每个AI Cube Core计算单元上后，每个AI Cube Core计算单元上的执行时间，单位us。</td></tr><tr><td>aic_total_cycles</td><td>该Task被分配到每个AI Cube Core计算单元上后，每个AI Cube Core计算单元上的执行的cycle总数。</td></tr><tr><td>aiv_time(us)</td><td>该Task被分配到每个AI Vector Core计算单元上后，每个AI Vector Core计算单元上的执行时间，单位us。</td></tr><tr><td>aiv_total_cycles</td><td>该Task被分配到每个AI Vector Core计算单元上后，每个AI Vector Core计算单元上的执行的cycle总数。</td></tr><tr><td>aiv ub_to_gm_bw(GB/s)</td><td>代表UB向GM写入的带宽速率，单位GB/s。</td></tr><tr><td>aiv_gm_to ub_bw(GB/s)</td><td>代表GM向UB写入的带宽速率，单位GB/s。</td></tr><tr><td>aic_l1_read_bw(GB/s)</td><td>代表l1读带宽速率，单位GB/s。</td></tr><tr><td>aic_l1_write_bw(GB/s)</td><td>代表l1写带宽速率，单位GB/s。</td></tr><tr><td>ai*main_mem_read_bw(GB/s)</td><td>代表主存储器读带宽速率，单位GB/s。</td></tr><tr><td>ai*main_mem_write_bw(GB/s)</td><td>代表主存储器写带宽速率，单位GB/s。</td></tr><tr><td>aic_mte1 Instructions</td><td>代表MTE1类型指令条数。</td></tr><tr><td>aic_mte1_ratio</td><td>代表MTE1类型指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>ai*_mte2 Instructions</td><td>代表MTE2类型指令条数。</td></tr><tr><td>ai*_mte2_ratio</td><td>代表MTE2类型指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>ai*_mte3 Instructions</td><td>代表MTE3类型指令条数。</td></tr><tr><td>ai*_mte3_ratio</td><td>代表MTE3类型指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>read_main_memory datas(KB)</td><td>读主存储器数据总量。</td></tr><tr><td>write_main_memory datas(KB)</td><td>写主存储器数据总量。</td></tr><tr><td>GM_to_L1 datas(KB)</td><td>GM到L1的数据搬运量。</td></tr><tr><td>L1_to_GMdatas(KB)(estimate)</td><td>L1到GM的数据搬运量，估算值。</td></tr><tr><td>LOC_to_L1 datas(KB)</td><td>LOC到L1的数据搬运量。</td></tr><tr><td>LOC_to_GMdatas(KB)</td><td>LOC到GM的数据搬运量。</td></tr><tr><td>GM_to UB datas(KB)</td><td>GM到UB的数据搬运量。</td></tr><tr><td>UB_to_GMdatas(KB)</td><td>UB到GM的数据搬运量。</td></tr><tr><td>GM_to_L1_bwusage_rater(%)</td><td>GM到L1通路带宽使用率。</td></tr><tr><td>L1_to_GM_bw_USAGE_rater(%) (estimate)</td><td>L1到GM通路带宽使用率，估算值。</td></tr><tr><td>LOC_to_L1_bw_USAGE_rater(%)</td><td>LOC到L1通路带宽使用率。</td></tr><tr><td>LOC_to_GM_bw_USAGE_rater(%)</td><td>LOC到GM通路带宽使用率。</td></tr><tr><td>GM_to UB_bw_USAGE_rater(%)</td><td>GM到UB通路带宽使用率。</td></tr><tr><td>UB_to_GM_bw_USAGE_rater(%)</td><td>UB到GM通路带宽使用率。</td></tr></table>

# Atlas 推理系列产品


图 8-17 Memory.csv 文件


<table><tr><td rowspan="2">aic_time(u)</td><td rowspan="2">aic_total_CYCLES</td><td>aic_1L_read_bw/G</td><td>aic_1L_write_bw/G</td><td>aic_1b_read_bw/G</td><td>aic_1b_write_bw/G</td><td>aic_main_mem_s</td><td>aic_main_mem_w</td><td>aic_mte1_Instructi</td><td>aic_mte1_ratio</td><td>aic_mte2_Instructi</td><td>aic_mte2_ratio</td><td>aic_mte3_Instructi</td><td>aic_mte3_ratio</td></tr><tr><td>B/s)</td><td>B/s)</td><td>GB/s)</td><td>GB/s)</td><td>read_bw/G</td><td>rte_bw/G</td><td>s/8</td><td>ons</td><td>80</td><td>0.706242</td><td>32</td><td>0.309224</td></tr><tr><td>4.322174</td><td>39764</td><td>0</td><td>0</td><td>367.735667</td><td>529.138855</td><td>7.312376</td><td>3.53035</td><td>0</td><td>0</td><td>0</td><td>0.706242</td><td>32</td><td>0.309224</td></tr></table>

关键字段说明如下。 


表 8-18 字段说明


<table><tr><td>字段名</td><td>字段解释</td></tr><tr><td>aic_time(us)</td><td>该Task被分配到每个AI Core计算单元上后，每个AI Core计算单元上的执行时间，单位us。</td></tr><tr><td>aic_total_cycles</td><td>该Task被分配到每个AI Core计算单元上后，每个AI Core计算单元上的执行的cycle总数。</td></tr><tr><td>aic ub_to_gm_bw(GB/s)</td><td>代表UB向GM写入的带宽速率，单位GB/s。</td></tr><tr><td>aic_gm_to ub_bw(GB/s)</td><td>代表GM向UB写入的带宽速率，单位GB/s。</td></tr><tr><td>aic_l1_read_bw(GB/s)</td><td>代表l1读带宽速率，单位GB/s。</td></tr><tr><td>aic_l1_write_bw(GB/s)</td><td>代表l1写带宽速率，单位GB/s。</td></tr><tr><td>aic_main_mem_read_bw(GB/s)</td><td>代表主存储器读带宽速率，单位GB/s。</td></tr><tr><td>aic_main_mem_write_bw(GB/s)</td><td>代表主存储器写带宽速率，单位GB/s。</td></tr><tr><td>aic_mte1InstructionS</td><td>代表MTE1类型指令条数。</td></tr><tr><td>aic_mte1_ratio</td><td>代表MTE1类型指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>aic_mte2InstructionS</td><td>代表MTE2类型指令条数。</td></tr><tr><td>aic_mte2_ratio</td><td>代表MTE2类型指令的cycle数在total cycle数中的占用比。</td></tr><tr><td>aic_mte3InstructionS</td><td>代表MTE3类型指令条数。</td></tr><tr><td>aic_mte3_ratio</td><td>代表MTE3类型指令的cycle数在total cycle数中的占用比。</td></tr></table>

# 8.11.1.4 MemoryL0（L0 读写带宽速率）

L0A/L0B/L0C采集内存读写带宽速率数据MemoryL0.csv。详情介绍请参见下表中的字 段说明。 

# Atlas A3 训练系列产品/Atlas A3 推理系列产品及 Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件


图 8-18 MemoryL0.csv 文件


<table><tr><td>block_id</td><td>sub_block_id</td><td>aic_time(u s)</td><td>aic_total_c ycles</td><td>aic_10a_re ad_bw(GB /s)</td><td>aic_10aWr ite_bw(GB /s)</td><td>aic_10b_re ad_bw(GB /s)</td><td>aic_10bWr ite_bw(GB /s)</td><td>aic_10c_re ad_bw_cu be(GB/s)</td><td>aic_10c_wri te_bw_cu be(GB/s)</td><td>aiv_time(u s)</td><td>aiv_total_c ycles</td></tr><tr><td>0</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.092727</td><td>8403</td></tr><tr><td>1</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.172727</td><td>8535</td></tr><tr><td>2</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.271515</td><td>8698</td></tr><tr><td>3</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.093333</td><td>8404</td></tr><tr><td>4</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.141212</td><td>8483</td></tr><tr><td>5</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.299394</td><td>8744</td></tr><tr><td>6</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.161212</td><td>8516</td></tr><tr><td>7</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5.240606</td><td>8647</td></tr></table>

关键字段说明如下。 


表 8-19 字段说明


<table><tr><td>字段名</td><td>字段解释</td></tr><tr><td>block_id</td><td>Task运行切分数量，对应Task运行时配置的核数。</td></tr><tr><td>sub_block_id</td><td>Task运行使用的每个block名称和序号。</td></tr><tr><td>aic_time(us)</td><td>该Task被分配到每个AI Cube Core计算单元上后，每个AI Cube Core计算单元上的执行时间，单位us。</td></tr><tr><td>aic_total_cycles</td><td>该Task被分配到每个AI Cube Core计算单元上后，每个AI Cube Core计算单元上的执行的cycle总数。</td></tr><tr><td>aiv_time(us)</td><td>该Task被分配到每个AI Vector Core计算单元上后，每个AI Vector Core计算单元上的执行时间，单位us。</td></tr><tr><td>aiv_total_cycles</td><td>该Task被分配到每个AI Vector Core计算单元上后，每个AI Vector Core计算单元上的执行的cycle总数。</td></tr><tr><td>aic_l0a_read_bw(GB/s)</td><td>代表l0a读带宽速率，单位GB/s。</td></tr><tr><td>aic_l0a_write_bw(GB/s)</td><td>代表l0a写带宽速率，单位GB/s。</td></tr><tr><td>aic_l0b_read_bw(GB/s)</td><td>代表l0b读带宽速率，单位GB/s。</td></tr><tr><td>aic_l0b_write_bw(GB/s)</td><td>代表l0b写带宽速率，单位GB/s。</td></tr><tr><td>aic_l0c_read_bw_cube(GB/s)</td><td>代表cube从l0c读带宽速率，单位GB/s。</td></tr><tr><td>aic_l0c_write_bw_cube(GB/s)</td><td>代表cube向l0c写带宽速率，单位GB/s。</td></tr></table>

# Atlas 推理系列产品


图 8-19 MemoryL0.csv 文件


<table><tr><td>aic_time(us)</td><td>aic_total cyclists</td><td>aic_10a_read_bw(GB/s)</td><td>aic_10a_write_bw(GB/s)</td><td>aic_10b_read_bw(GB/s)</td><td>aic_10b_write_bw(GB/s)</td><td>aic_10c_read_bw_cube(GB/s)</td><td>aic_10c_write_bw_cube(GB/s)</td><td>aic_10c_read_bw(GB/s)</td><td>aic_10c_write_bw(GB/s)</td></tr><tr><td>4.322174</td><td>39764</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr></table>

关键字段说明如下。 


表 8-20 字段说明


<table><tr><td>字段名</td><td>字段解释</td></tr><tr><td>aic_time(us)</td><td>该Task被分配到每个AI Core计算单元上后，每个AI Core计算单元上的执行时间，单位us。</td></tr><tr><td>aic_total_cycles</td><td>该Task被分配到每个AI Core计算单元上后，每个AI Core计算单元上的执行的cycle总数。</td></tr><tr><td>aic_l0a_read_bw(GB/s)</td><td>代表l0a读带宽速率，单位GB/s。</td></tr><tr><td>aic_l0a_write_bw(GB/s)</td><td>代表l0a写带宽速率，单位GB/s。</td></tr><tr><td>aic_l0b_read_bw(GB/s)</td><td>代表l0b读带宽速率，单位GB/s。</td></tr><tr><td>aic_l0b_write_bw(GB/s)</td><td>代表l0b写带宽速率，单位GB/s。</td></tr><tr><td>aic_l0c_read_bw_cube(GB/s)</td><td>代表cube从l0c读带宽速率，单位GB/s。</td></tr><tr><td>aic_l0c_write_bw_cube(GB/s)</td><td>代表cube向l0c写带宽速率，单位GB/s。</td></tr><tr><td>aic_l0c_read_bw(GB/s)</td><td>代表vector从l0c读带宽速率，单位GB/s。</td></tr><tr><td>aic_l0c_write_bw(GB/s)</td><td>代表vector向l0c写带宽速率，单位GB/s。</td></tr></table>

# 8.11.1.5 MemoryUB（UB 读写带宽速率）

mte/vector/scalar采集ub读写带宽速率数据MemoryUB.csv。详情介绍请参见下表中 的字段说明。 

# Atlas A3 训练系列产品/Atlas A3 推理系列产品及 Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件


图 8-20 MemoryUB.csv 文件


<table><tr><td>block_id</td><td>sub_block_id</td><td>aic_time(u s)</td><td>aic_total_c ycles</td><td>aiv_time(u s)</td><td>aiv_total_c ycles</td><td>aiv ub_re ad_bw_vec tor(GB/s)</td><td>aiv ub_wri te_bw_vec tor(GB/s)</td><td>aiv ub_re ad_bw_sc alar(GB/s)</td><td>aiv ub_wri te_bw_sca lar(GB/s)</td></tr><tr><td>0</td><td>vector0</td><td>N/A</td><td>N/A</td><td>5.092727</td><td>8403</td><td>1.498096</td><td>0.749048</td><td>0</td><td>0</td></tr><tr><td>1</td><td>vector0</td><td>N/A</td><td>N/A</td><td>5.172727</td><td>8535</td><td>1.474927</td><td>0.737463</td><td>0</td><td>0</td></tr><tr><td>2</td><td>vector0</td><td>N/A</td><td>N/A</td><td>5.271515</td><td>8698</td><td>1.447287</td><td>0.723643</td><td>0</td><td>0</td></tr><tr><td>3</td><td>vector0</td><td>N/A</td><td>N/A</td><td>5.093333</td><td>8404</td><td>1.497918</td><td>0.748959</td><td>0</td><td>0</td></tr><tr><td>4</td><td>vector0</td><td>N/A</td><td>N/A</td><td>5.141212</td><td>8483</td><td>1.483968</td><td>0.741984</td><td>0</td><td>0</td></tr><tr><td>5</td><td>vector0</td><td>N/A</td><td>N/A</td><td>5.299394</td><td>8744</td><td>1.439673</td><td>0.719836</td><td>0</td><td>0</td></tr><tr><td>6</td><td>vector0</td><td>N/A</td><td>N/A</td><td>5.161212</td><td>8516</td><td>1.478218</td><td>0.739109</td><td>0</td><td>0</td></tr><tr><td>7</td><td>vector0</td><td>N/A</td><td>N/A</td><td>5.240606</td><td>8647</td><td>1.455823</td><td>0.727912</td><td>0</td><td>0</td></tr></table>

关键字段说明如下。 


表 8-21 字段说明


<table><tr><td>字段名</td><td>字段解释</td></tr><tr><td>block_id</td><td>Task运行切分数量，对应Task运行时配置的核数。</td></tr><tr><td>sub_block_id</td><td>Task运行使用的每个block名称和序号。</td></tr><tr><td>aic_time(us)</td><td>该Task被分配到每个AI Cube Core计算单元上后，每个AI Cube Core计算单元上的执行时间，单位us。</td></tr><tr><td>aic_total_cycles</td><td>该Task被分配到每个AI Cube Core计算单元上后，每个AI Cube Core计算单元上的执行的cycle总数。</td></tr><tr><td>aiv_time(us)</td><td>该Task被分配到每个AI Vector Core计算单元上后，每个AI Vector Core计算单元上的执行时间，单位us。</td></tr><tr><td>aiv_total_cycles</td><td>该Task被分配到每个AI Vector Core计算单元上后，每个AI Vector Core计算单元上的执行的cycle总数。</td></tr><tr><td>aiv_ub_read_bw_vector(r(GB/s)</td><td>代表vector从UB读带宽速率，单位GB/s。</td></tr><tr><td>aiv_ub_write_bw_vector(r(GB/s)</td><td>代表vector向UB写带宽速率，单位GB/s。</td></tr><tr><td>aiv_ub_read_bwscalars(r(GB/s)</td><td>代表scalar从UB读带宽速率，单位GB/s。</td></tr><tr><td>aiv_ub_write_bwscalars(r(GB/s)</td><td>代表scalar向UB写带宽速率，单位GB/s。</td></tr></table>

# Atlas 推理系列产品


图 8-21 MemoryUB.csv 文件


<table><tr><td>aic_time(us)</td><td>aic_total_cycles</td><td>aic_ub_read_b
wSCRAR(GB/s)</td><td>aic_ub_write_b
wSCRAR(GB/s)</td><td>aic_ub_read_b
w_vector(GB/s)</td><td>aic_ub_write_b
w_vector(GB/s)</td></tr><tr><td>4.322174</td><td>39764</td><td>0.220647</td><td>0</td><td>50.086849</td><td>28.242804</td></tr></table>

关键字段说明如下。 


表 8-22 字段说明


<table><tr><td>字段名</td><td>字段解释</td></tr><tr><td>aic_time(us)</td><td>该Task被分配到每个AI Core计算单元上后，每个AI Core计算单元上的执行时间，单位us。</td></tr><tr><td>aic_total_cycles</td><td>该Task被分配到每个AI Core计算单元上后，每个AI Core计算单元上的执行的cycle总数。</td></tr><tr><td>aic UB_read_bw_vector(GB/s)</td><td>代表vector从UB读带宽速率，单位GB/s。</td></tr><tr><td>aic UB_write_bw_vector(r(GB/s)</td><td>代表vector向UB写带宽速率，单位GB/s。</td></tr><tr><td>aic UB_read_bwCSR(GB/s)</td><td>代表scalar从UB读带宽速率，单位GB/s。</td></tr><tr><td>aic UB_write_bw scalars(GB/s)</td><td>代表scalar向UB写带宽速率，单位GB/s。</td></tr></table>

# 8.11.1.6 OpBasicInfo（算子基础信息）

算子基础信息数据OpBasicInfo.csv，包含算子名称，算子类型，Block Dim和耗时等信 息。详情介绍请参见下表中的字段说明。 


图 8-22 OpBasicInfo.csv 文件


<table><tr><td>Op Name</td><td>Op Type</td><td>Task Duration(us)</td><td>Block Dim</td><td>Mix Block Dim</td><td>Device Id</td><td>Pid</td><td>Current Freq</td><td>Rated Freq</td></tr><tr><td>matmul_leakyrelu_custom_0_mix_acic</td><td>mix</td><td>157.600006</td><td>2</td><td>4</td><td>0</td><td>521012</td><td>800</td><td>1650</td></tr></table>

关键字段说明如下。 


表 8-23 字段说明


<table><tr><td>字段名</td><td>字段解释</td></tr><tr><td>Op Name</td><td>算子名称。</td></tr><tr><td>Op Type</td><td>算子类型。</td></tr><tr><td>Task Duration(us)</td><td>Task耗时，包含调度到昇腾AI处理器的时间、昇腾AI处理器上的执行时间以及结束响应时间，单位us。</td></tr><tr><td>Block Dim</td><td>Task运行切分数量，对应Task运行时核数，开发者设置的算子执行逻辑核数。</td></tr><tr><td>Mix Block Dim</td><td>部分算子同时在Cube Core和Vector Core上执行，主昇腾AI处理器的blockDim在Block Dim字段描述，从昇腾AI处理器的blockDim在本字段描述。显示为N/A表示为非Mix融合算子。
说明
此参数仅适用于Atlas A3训练系列产品/Atlas A3推理系列产品和Atlas A2训练系列产品/Atlas 800I A2推理产品/A200I A2 Box异构组件。</td></tr><tr><td>Device ID</td><td>运行时使用昇腾AI处理器的ID。</td></tr><tr><td>PID</td><td>算子运行时的进程号。</td></tr><tr><td>Current Freq</td><td>昇腾AI处理器当前运行的频率。</td></tr><tr><td>Rated Freq</td><td>昇腾AI处理器的理论频率。</td></tr></table>

# 8.11.1.7 PipeUtilization（计算单元和搬运单元耗时占比）

采集计算单元和搬运单元耗时和占比数据PipeUtilization.csv。建议优化数据搬运逻 辑，提高带宽利用率。详情介绍请参见下表中的字段说明。 

# Atlas A3 训练系列产品/Atlas A3 推理系列产品及 Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件


图 8-23 PipeUtilization.csv 文件


<table><tr><td>block_id</td><td>sub block_id</td><td>icc</td><td>trecu</td><td>icc total</td><td>icc max</td><td>icc curve</td><td>i max</td><td>icc curve +</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc max</td><td>icc min</td><td>icc max</td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td><td>yolo</td></tr><tr><td>0</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td></td><td></td></tr><tr><td>1</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td></td><td></td><td></td><td></td></tr><tr><td>2</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td></td><td></td><td></td><td></td></tr><tr><td>3</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td colspan="2">N/A</td><td></td><td></td><td></td></tr><tr><td>4</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td></td><td></td><td></td><td></td></tr><tr><td>5</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td></td><td></td><td></td><td></td></tr></table>

关键字段说明如下。 


表 8-24 字段说明


<table><tr><td>字段名</td><td>字段解释</td></tr><tr><td>block_id</td><td>Task运行切分数量，对应Task运行时配置的核数。</td></tr><tr><td>sub_block_id</td><td>Task运行使用的每个block名称和序号。</td></tr><tr><td>aic_time(us)</td><td>该Task被分配到每个AI Cube Core计算单元上后，每个AI Cube Core计算单元上的执行时间，单位us。</td></tr><tr><td>aic_total_cycles</td><td>该Task被分配到每个AI Cube Core计算单元上后，每个AI Cube Core计算单元上的执行的cycle总数。</td></tr><tr><td>aiv_time(us)</td><td>该Task被分配到每个AI Vector Core计算单元上后，每个AI Vector Core计算单元上的执行时间，单位us。</td></tr><tr><td>aiv_total_cycles</td><td>该Task被分配到每个AI Vector Core计算单元上后，每个AI Vector Core计算单元上的执行的cycle总数。</td></tr><tr><td>aiv_vec_time(us)</td><td>代表vec类型指令（向量类运算指令）耗时。</td></tr><tr><td>aiv_vec_ratio</td><td>代表vec类型指令（向量类运算指令）的cycle数在total cycle数中的占用比。</td></tr><tr><td>aic_cube_time(us)</td><td>代表cube类型指令（fp16及s16矩阵类运算指令）耗时。</td></tr><tr><td>aic_cube_ratio</td><td>代表cube类型指令（fp16及s16矩阵类运算指令）的cycle数在total cycle数中的占用比。</td></tr><tr><td>ai*scalar_time(us)</td><td>代表scalar类型指令（标量类运算指令）耗时。</td></tr><tr><td>ai*scalar_ratio</td><td>代表scalar类型指令（标量类运算指令）的cycle数在total cycle数中的占用比。</td></tr><tr><td>aic_fixpipe_time(us)</td><td>代表fixpipe类型指令（LOC-&gt;GM/L1搬运类指令）耗时。</td></tr><tr><td>aic_fixpipe_ratio</td><td>代表fixpipe类型指令（LOC-&gt;GM/L1搬运类指令）的cycle数在total cycle数中的占用比。</td></tr><tr><td>aic_mte1_time(us)</td><td>代表MTE1类型指令（L1-&gt;L0A/L0B搬运类指令）耗时，不包括搬运等待时间。</td></tr><tr><td>aic_mte1_ratio</td><td>代表MTE1类型指令（L1-&gt;L0A/L0B搬运类指令）的cycle数在total cycle数中的占用比。</td></tr><tr><td>ai*_mte2_time(us)</td><td>代表MTE2类型指令（GM-&gt;AICORE搬运类指令）耗时。</td></tr><tr><td>ai*_mte2_ratio</td><td>代表MTE2类型指令（GM-&gt;AICORE搬运类指令）的cycle数在total cycle数中的占用比。</td></tr><tr><td>ai*_mte3_time(us)</td><td>代表MTE3类型指令（AICORE-&gt;GM搬运类指令）耗时。</td></tr><tr><td>ai*_mte3_ratio</td><td>代表MTE3类型指令（AICORE-&gt;GM搬运类指令）的cycle数在total cycle数中的占用比。</td></tr><tr><td>ai* icache_miss_r ate</td><td>代表ICache缺失率，即未命中instruction的L1 cache，数值越小越好。</td></tr></table>

# Atlas 推理系列产品


图 8-24 PipeUtilization.csv 文件


<table><tr><td></td><td>A</td><td>B</td><td>C</td><td>D</td><td>E</td><td>F</td><td>G</td><td>H</td><td>I</td><td>J</td><td>K</td><td>L</td><td>M</td><td>N</td><td>O</td></tr><tr><td>1</td><td>aic_time(u s)</td><td>aic_total_c ycles</td><td>aic_cube_t ime(u)</td><td>aic_cube_r atio</td><td>aicscalar_time(u)</td><td>aicscalar_ratio</td><td>aic,mte1_t ime(u)</td><td>aic,mte1_r atio</td><td>aic,mte2_t ime(u)</td><td>aic,mte2_r atio</td><td>aic,mte3_t ime(u)</td><td>aic,mte3_r atio</td><td>aic,jcache _miss_rate</td><td>aic_VEC_t i me(u)</td><td>aic_VEC_ra tio</td></tr><tr><td>2</td><td>4.322174</td><td>39764</td><td>0</td><td>0</td><td>0.468804</td><td>0.108465</td><td>0</td><td>0</td><td>3.0525</td><td>0.706242</td><td>1.336522</td><td>0.309224</td><td>0.022672</td><td>0.841739</td><td>0.194749</td></tr></table>

关键字段说明如下。 


表 8-25 字段说明


<table><tr><td>字段名</td><td>字段解释</td></tr><tr><td>aic_time(us)</td><td>该Task被分配到每个AI Core计算单元上后，每个AI Core计算单元上的执行时间，单位us。</td></tr><tr><td>aic_total_cycle</td><td>该Task被分配到每个AI Core计算单元上后，每个AI Core计算单元上的执行的cycle总数。</td></tr><tr><td>aic_cube_time( us)</td><td>代表cube类型指令（fp16及s16矩阵类运算指令）耗时。</td></tr><tr><td>aic_cube_ratio</td><td>代表cube类型指令（fp16及s16矩阵类运算指令）的cycle数在 total cycle数中的占用比。</td></tr><tr><td>aicSCRalar_time( us)</td><td>代表scalar类型指令（标量类运算指令）耗时。</td></tr><tr><td>aicSCRalar_rati o</td><td>代表scalar类型指令（标量类运算指令）的cycle数在total cycle数中的占用比。</td></tr><tr><td>aic_mte1_time( us)</td><td>代表MTE1类型指令（L1-&gt;L0A/L0B搬运类指令）耗时，不包括搬运等待时间。</td></tr><tr><td>aic_mte1_ratio</td><td>代表MTE1类型指令（L1-&gt;L0A/L0B搬运类指令）的cycle数在 total cycle数中的占用比。</td></tr><tr><td>aic_mte2_time( us)</td><td>代表MTE2类型指令（GM-&gt;AICORE搬运类指令）耗时。</td></tr><tr><td>aic_mte2_ratio</td><td>代表MTE2类型指令（GM-&gt;AICORE搬运类指令）的cycle数在 total cycle数中的占用比。</td></tr><tr><td>aic_mte3_time( us)</td><td>代表MTE3类型指令（AICORE-&gt;GM搬运类指令）耗时。</td></tr><tr><td>aic_mte3_ratio</td><td>代表MTE3类型指令（AICORE-&gt;GM搬运类指令）的cycle数在 total cycle数中的占用比。</td></tr><tr><td>aic_icache_miss_rate</td><td>代表ICache缺失率，即未命中instruction的L1 cache，数值越小越好。</td></tr><tr><td>aic_vec_time( us)</td><td>代表vec类型指令（向量类运算指令）耗时。</td></tr><tr><td>aic_vec_ratio</td><td>代表vec类型指令（向量类运算指令）的cycle数在total cycle数中的占用比。</td></tr></table>

# 8.11.1.8 ResourceConflictRatio（资源冲突占比）

UB上的bank group、bank conflict和资源冲突在所有指令中的占比数据 ResourceConflictRatio.csv，建议减少对于同一个bank的读写冲突或bank group的读 读冲突。 

bank group是指UB中的一组bank，每个bank group包含多个bank。bank conflict是 指在UB中同时访问相同bank的多个线程之间的竞争。 

详情介绍请参见下表中的字段说明。 

# Atlas A3 训练系列产品/Atlas A3 推理系列产品及 Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件


图 8-25 ResourceConflictRatio.csv 文件


<table><tr><td>block_id</td><td>sub_block_id</td><td>aic_time(u_s)</td><td>aic_total_cycles</td><td>aic CubeWait ratio</td><td>aic_mte1Wait ratio</td><td>aic_mte2Wait ratio</td><td>aic_mte3Wait ratio</td><td>aic_time(u_s)</td><td>aic_total_cycles</td><td>aic_vec_tal_cft_ratio</td><td>aic_vec_bank_talt_tsc_tat_tct_tatio</td><td>aic_vec_bank_tct_tra_tio</td><td>aic_vec_re_tsc_tat_tce_tcat_tatio</td><td>aic_vec_w_tai_ratio</td><td>aic_mte1Wait ratio</td><td>aic_mte2Wait ratio</td><td>aic_mte3Wait ratio</td><td></td></tr><tr><td>0</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5092777</td><td>8403</td><td>0.001904</td><td>0.001904</td><td>0</td><td>0</td><td>0</td><td>0.489706</td><td>0</td><td>0.090563</td><td>0.333571</td></tr><tr><td>1</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5172727</td><td>8535</td><td>0.001875</td><td>0.001875</td><td>0</td><td>0</td><td>0</td><td>0.559993</td><td>0</td><td>0.269127</td><td>0.462449</td></tr><tr><td>2</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5271515</td><td>8698</td><td>0.00184</td><td>0.00184</td><td>0</td><td>0</td><td>0</td><td>0.542309</td><td>0</td><td>0.224419</td><td>0.439526</td></tr><tr><td>3</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5093333</td><td>8404</td><td>0.001904</td><td>0.001904</td><td>0</td><td>0</td><td>0</td><td>0.551523</td><td>0</td><td>0.19574</td><td>0.435626</td></tr><tr><td>4</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5141212</td><td>8483</td><td>0.001886</td><td>0.001886</td><td>0</td><td>0</td><td>0</td><td>0.573971</td><td>0</td><td>0.235058</td><td>0.497348</td></tr><tr><td>5</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5299394</td><td>8744</td><td>0.00183</td><td>0.00183</td><td>0</td><td>0</td><td>0</td><td>0.570563</td><td>0</td><td>0.300892</td><td>0.481016</td></tr><tr><td>6</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5161212</td><td>8516</td><td>0.001879</td><td>0.001879</td><td>0</td><td>0</td><td>0</td><td>0.467003</td><td>0</td><td>0.01914</td><td>0.272311</td></tr><tr><td>7</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>5240606</td><td>8647</td><td>0.00185</td><td>0.00185</td><td>0</td><td>0</td><td>0</td><td>0.414826</td><td>0</td><td>0</td><td>0.214294</td></tr></table>

关键字段说明如下。 


表 8-26 字段说明


<table><tr><td>字段名</td><td>字段解释</td></tr><tr><td>block_id</td><td>Task运行切分数量，对应Task运行时配置的核数。</td></tr><tr><td>sub_block_id</td><td>Task运行使用的每个block名称和序号。</td></tr><tr><td>aic_time(us)</td><td>该Task被分配到每个AI Cube Core计算单元上后，每个AI Cube Core计算单元上的执行时间，单位us。</td></tr><tr><td>aic_total_cycles</td><td>该Task被分配到每个AI Cube Core计算单元上后，每个AI Cube Core计算单元上的执行的cycle总数。</td></tr><tr><td>aiv_time(us)</td><td>该Task被分配到每个AI Vector Core计算单元上后，每个AI Vector Core计算单元上的执行时间，单位us。</td></tr><tr><td>aiv_total_cycles</td><td>该Task被分配到每个AI Vector Core计算单元上后，每个AI Vector Core计算单元上的执行的cycle总数。</td></tr><tr><td>aic_cube_wait_ratio</td><td>代表cube单元被阻塞的cycle数在所有指令执行cycle数中占比。</td></tr><tr><td>aiv_vec_total_cflt_ratio</td><td>代表所有vector执行的指令被阻塞的cycle数在所有指令执行cycle数中占比。</td></tr><tr><td>aiv_vec_bankgroup_cflt_ratio</td><td>代表vector执行的指令被bankgroup冲突阻塞的cycle数在所有指令执行cycle数中占比。由于Vector指令的block stride的值设置不合理，造成bankgroup冲突。</td></tr><tr><td>aiv_vec_bank_cflt_ratio</td><td>代表vector执行的指令被bank冲突阻塞的cycle数在所有指令执行cycle数中占比。由于Vector指令操作数的读写指针地址不合理，造成bank冲突。</td></tr><tr><td>aiv_vec_resc_cflt_ratio</td><td>代表vector执行的指令被执行单元资源冲突阻塞的cycle数在所有指令执行cycle数中占比。当算子中涉及多个计算单元，应该尽量保证多个单元并发调度。当某个计算单元正在运行，但算子逻辑仍然往该单元下发指令，就会造成整体的算力没有得到充分应用。</td></tr><tr><td>aiv_vec_mte_cflt_ratio</td><td>代表vector执行的指令被MTE冲突阻塞的cycle数在所有指令执行cycle数中占比。</td></tr><tr><td>aiv_vec_wait_ratio</td><td>代表vector单元被阻塞的cycle数在所有指令执行cycle数中占比。</td></tr><tr><td>ai*_mte1_wait_ratio</td><td>代表MTE1被阻塞的cycle数在所有指令执行cycle数中占比。</td></tr><tr><td>ai*_mte2_wait_ratio</td><td>代表MTE2被阻塞的cycle数在所有指令执行cycle数中占比。</td></tr><tr><td>ai*_mte3_wait_ratio</td><td>代表MTE3被阻塞的cycle数在所有指令执行cycle数中占比。</td></tr></table>

# Atlas 推理系列产品


图 8-26 ResourceConflictRatio.csv 文件


<table><tr><td></td><td>A</td><td>B</td><td>C</td><td>D</td><td>E</td><td>F</td><td>G</td><td>H</td><td>I</td><td>J</td><td>K</td><td>L</td></tr><tr><td>1</td><td>aic_time(us)</td><td>aic_total_CYCLES</td><td>aic Cube_wait_ratiO</td><td>aic_vez_wait_ratiO</td><td>aic_mte1_wait_ratiO</td><td>aic_mte2_wait_ratiO</td><td>aic_mte3_wait_ratiO</td><td>aic_vez_total_cft_tatio</td><td>aic_vez_bankgro_up_cft_ratio</td><td>aic_vez_bank_cft_tatio</td><td>aic_vez_res_cft_tatio</td><td>aic_vez_mte_cft_tatio</td></tr><tr><td>2</td><td>4.3222174</td><td>39764</td><td>0</td><td>0.656976</td><td>0</td><td>0.351524</td><td>0.704381</td><td>0.07967</td><td>0</td><td>0.07967</td><td>0</td><td>0</td></tr></table>

关键字段说明如下。 


表8-27 字段说明


<table><tr><td>字段名</td><td>字段解释</td></tr><tr><td>aic_time(us)</td><td>该Task被分配到每个AI Core计算单元上后，每个AI Core计算单元上的执行时间，单位us。</td></tr><tr><td>aic_total_cycles</td><td>该Task被分配到每个AI Core计算单元上后，每个AI Core计算单元上的执行的cycle总数。</td></tr><tr><td>aic_cube_wait_ratio</td><td>代表cube单元被阻塞的cycle数在所有指令执行cycle数中占比。</td></tr><tr><td>aic_vec_total_cfl_t_ratio</td><td>代表所有vector执行的指令被阻塞的cycle数在所有指令执行cycle数中占比。</td></tr><tr><td>aic_vec_bankgroup_cflt_ratio</td><td>代表vector执行的指令被bankgroup冲突阻塞的cycle数在所有指令执行cycle数中占比。由于Vector指令的block stride的值设置不合理，造成bankgroup冲突。</td></tr><tr><td>aic_vec_bank_cflt_ratio</td><td>代表vector执行的指令被bank冲突阻塞的cycle数在所有指令执行cycle数中占比。由于Vector指令操作数的读写指针地址不合理，造成bank冲突。</td></tr><tr><td>aic_vec_resc_cflt_ratio</td><td>代表vector执行的指令被执行单元资源冲突阻塞的cycle数在所有指令执行cycle数中占比。当算子中涉及多个计算单元，应该尽量保证多个单元并发调度。当某个计算单元正在运行，但算子逻辑仍然往该单元下发指令，就会造成整体的算力没有得到充分应用。</td></tr><tr><td>aic_vec_mte_cflt_ratio</td><td>代表vector执行的指令被MTE冲突阻塞的cycle数在所有指令执行cycle数中占比。</td></tr><tr><td>aic_vec_wait_rati0</td><td>代表vector单元被阻塞的cycle数在所有指令执行cycle数中占比。</td></tr><tr><td>aic_mte1_wait_rati0</td><td>代表MTE1被阻塞的cycle数在所有指令执行cycle数中占比。</td></tr><tr><td>aic_mte2_wait_rati0</td><td>代表MTE2被阻塞的cycle数在所有指令执行cycle数中占比。</td></tr><tr><td>aic_mte3_wait_rati0</td><td>代表MTE3被阻塞的cycle数在所有指令执行cycle数中占比。</td></tr></table>

# 8.11.2 msprof op simulator

# 8.11.2.1 代码行耗时数据文件

代码行耗时数据文件core*_code_exe.csv。 

core*.veccore* 或core*.cubecore*目录下存放各计算单元的代码行耗时文件，例如 core0.veccore1目录下的core0.veccore1_code_exe.csv文件，“core0”代表核编号， “veccore1”代表子核编号。 


图 8-27 core*_code_exe.csv 文件


<table><tr><td>code</td><td>call_count</td><td>cycles</td><td colspan="2">running_time(us)</td></tr><tr><td>/home/zha</td><td>5377</td><td>62388.5</td><td>6.01</td><td></td></tr><tr><td>/home/zha</td><td>454</td><td>29890.5</td><td>1.05</td><td></td></tr><tr><td>/home/zha</td><td>454</td><td>29890.5</td><td>1.05</td><td></td></tr><tr><td>/home/zha</td><td>1744</td><td>23936</td><td>2.18</td><td></td></tr><tr><td>/home/zha</td><td>2208</td><td>23071</td><td>2.65</td><td></td></tr><tr><td>/home/zha</td><td>1344</td><td>15309</td><td>1.91</td><td></td></tr></table>

关键字段说明如下。 


表 8-28 字段说明


<table><tr><td>字段名</td><td>字段解释</td></tr><tr><td>code</td><td>代码行，格式为代码文件路径:行号。</td></tr><tr><td>call_count</td><td>对应代码行所涉及指令的调用次数。</td></tr><tr><td>cycles</td><td>该代码行所涉及的指令在AI Vector Core/Al Cube Core上执行的 cycle总数。</td></tr><tr><td>running_time (us)</td><td>代码行的有效执行时间，单位us。</td></tr></table>

# 8.11.2.2 代码指令信息文件

代码指令详细信息文件core*_instr_exe.csv。 

core*.veccore* 或core*.cubecore*目录下存放各计算单元的代码指令详细信息文件，例 如core0.veccore0目录下core0.veccore0_instr_exe.csv，“core0”代表核编号， “veccore0”代表子核编号。 


图 8-28 core*_instr_exe.csv 文件


<table><tr><td>instr</td><td>addr</td><td>pipe</td><td>call_count</td><td>cycles</td><td>running_time(us)</td><td>detail</td><td>6.6d 2,0dt UB,XD:X0=0,XD:X0,0XM:X2=0x20010,XM:X2x20010;XN:X1=0x10fc9400;XN:X1x010fc9400;Src:OUT</td></tr><tr><td>MOV_OUT</td><td>0x11fe3d0</td><td>MTE2</td><td>32</td><td>12486</td><td>7.66</td><td>1.6 IMM:0x7;XI:0x0=0x6;XI:0x0x6;XI:4=0x7;XI:4x0;XN:X5=0x163770;XN:X5x0163770;dtype B8</td><td></td></tr><tr><td>STP_XL_OL</td><td>0x11fe311</td><td>SCALAR</td><td>32</td><td>4037</td><td>1.66</td><td>IMM:0x5;XI:X9=0x4;XI:X9x0;XI:X10=0x5;XI:X10x5;XN:X5=0x163770;XN:X5x0163770; dtype B8</td><td></td></tr><tr><td>STP_XL_OL</td><td>0x11fe311</td><td>SCALAR</td><td>32</td><td>3482</td><td>1.66</td><td>IMM:0x5;XI:X9=0x4;XI:X9x0;XI:X10=0x5;XI:X10x5;XN:X5=0x163770;XN:X5x0163770; dtype B8</td><td></td></tr><tr><td>STP_XL_OL</td><td>0x11fe311</td><td>SCALAR</td><td>32</td><td>3246</td><td>1.66</td><td>IMM:0x3;XI:X6=0x2;XI:X6x0;XI:X7=0x3;XI:X7x0;XN:X5=0x163770;XN:X5x0163770; dtype B8</td><td></td></tr><tr><td>STL_XN_IM</td><td>0x11fe311</td><td>SCALAR</td><td>32</td><td>3333</td><td>1.65</td><td>#IMM_TYPE_ONE #POST:0 IMM:0x2;XN:X5=0x163770;XN:X5x0163770; dtype B8</td><td></td></tr><tr><td>STL_XN_IM</td><td>0x11fe310</td><td>SCALAR</td><td>32</td><td>3325</td><td>1.65</td><td>#IMM_TYPE_ZERO #POST:0 IMM:0x1;XN:X5=0x163770;XN:X5x0163770; dtype B8</td><td></td></tr><tr><td>STL_XN_IM</td><td>0x11fe310</td><td>SCALAR</td><td>32</td><td>3291</td><td>1.65</td><td>#IMM_TYPE_ZERO #POST:0 IMM:0;XN:X5=0x163770;XN:X5x0163770; dtype B8</td><td></td></tr></table>

关键字段说明如下。 


表 8-29 字段说明


<table><tr><td>字段名</td><td>字段解释</td></tr><tr><td>instr</td><td>代码指令名称。</td></tr><tr><td>addr</td><td>代码指令对应的PC地址。</td></tr><tr><td>pipe</td><td>PIPE类型，包括指令队列和计算单元。</td></tr><tr><td>call_count</td><td>该指令的调用次数。</td></tr><tr><td>cycles</td><td>该指令在AI Vector Core/Al Cube Core上执行的cycle总数。</td></tr><tr><td>running_time(us)</td><td>指令的有效执行时间，单位us。</td></tr><tr><td>detail</td><td>指令执行的详细参数。</td></tr></table>