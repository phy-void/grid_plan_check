## Synthesize:20201130

* 字符串用法：`string.lower()`全部改为小写。

* np.loadtxt()函数：
  -  `fname`要读取的文件、文件名、或生成器。
  -  `dtype`数据类型，默认float。
  -  `comments`注释。如果开头是#，这一行不被读取。
  -  `delimiter`分隔符，默认是空格。
  -  `skiprows`跳过前几行读取，默认是0，必须是int整型。
  -  `usecols`：要读取哪些列，0是第一列。例如，usecols = （1,4,5）将提取第2，第5和第6列。默认读取所有列。
  -  `unpack`如果为`True`，将分列读取。

```python
loadtxt(fname, dtype=, comments='#', delimiter=None, converters=None, skiprows=0, usecols=None, unpack=False, ndmin=0)
```

* 1e-100，这个用法就是10^-100^
* scipy.interpolate.griddata

```python
scipy.interpolate.griddata(points, values, xi, method='linear', fill_value=nan, rescale=False)
```

Parameters :

points: 2-D ndarray of floats with shape (n, D), or length D tuple of 1-D ndarrays with shape (n,).
Data point coordinates.

values: ndarray of float or complex, shape (n,)
Data values.

xi: 2-D ndarray of floats with shape (m, D), or length D tuple of ndarrays broadcastable to the same shape.
Points at which to interpolate data.

method: {‘linear’, ‘nearest’, ‘cubic’}, optional

Returns: ndarray
Array of interpolated values. 

* 所以为什么选用linear而不是cubic? 答：因为没有改原程序……   我这里再次总结一遍：interpolate.griddata这个插值函数的效果，简单来说就是把SAA标准地图上面的辐射值给投射到实际的轨道文件的对应坐标点上。使用了线性插值。可以print看一看。
* 再记一遍：right ascension赤经，declination赤纬。
  所以下面这个算地球的radec是怎么回事？**这里面的天球坐标究竟是怎么定义的？**

```python
earth_ra = orb_ra + np.pi
earth_dec = -orb_dec
```

已解决：相当于在卫星看来地球的位置，可以把卫星和地球认为都在原点，这样的话把原点移到卫星上也不会改变远处天体的RA DEC. by the way, 天球坐标使用的是J2000标准

* 通过find_continous_intervals和Is_too_short两个函数折腾完之后，得到观测目标可行的开始、结束的时间序列的index。
* 程序中是否做了类似把最后计算出来的时间和转向操作等以一种易读的方式输出，来得到一个直观的观测计划，这种？*已提上日程*。
* -y指的是太阳能电池板法线方向。
* st: star tracker星敏。一个类似拍照的设备，用于精确的姿态确定。在很多情况下都不工作。
* install package: pyquaternion-0.9.9
* 四元数计算的结果是一个角度，而非转向。这个角度发送后，卫星通过其他方式（我们不关心）可以调整到这个要求的姿态。这是工作机制。
* HV是什么的缩写？high voltage
* 试运行：已检查至开机时间计算部分，认为三部分时间计算有效：可观测时间（目标在地球遮挡外+可控制）、可姿控时间（有卫星使用权但观测角度被地球遮挡）、无控制时间。得到系列输出i为轨道时间序列orb_time的对应index。
* when blocked: grid_target，使用虚拟目标。如果是以卫星为原点的天球坐标系，虚拟元应该就是背对地球的方向吧？是。
* 探测器轴z、太阳能板法线y（应该是垂直的吧），两轴的方向确定卫星姿态。
* **卫星坐标系**问题：见图片satellite coordinate.png, 星敏自身的指向为(0,0,1), 用安装矩阵乘以它得到卫星坐标系中的指向：(0,sin18,-cos18). 此外，探测器指向为-z，太阳能板法线为-y。
* pl.radec_to_xyz函数就是球坐标系，球面r=1的坐标变换。
* np.cross函数：计算叉乘。
* 四元数的再学习：
  * 基本介绍：四元数都是由实数加上三个虚数单位 i、j、k 组成，而且它们有如下的关系： i^2 = j^2 = k^2 = -1， i^0 = j^0 = k^0 = 1 , 每个四元数都是 1、i、j 和 k 的线性组合，即是四元数一般可表示为a + bi+ cj + dk。对于i、j、k本身的几何意义可以理解为一种旋转，其中i旋转代表XY平面中X轴正向向Y轴正向的旋转，j旋转代表XZ平面中Z轴正向向X轴正向的旋转，k旋转代表YZ平面中Y轴正向向Z轴正向的旋转。
* 四元数旋转的简单应用：对于一个xyz向量(x, y, z), 以这个向量为轴旋转θ角，对应的四元数：cos(θ/2)+xsin(θ/2)·i+ysin(θ/2)·j+zsin(θ/2)·k. 把一个点w=(wx, wy, wz)进行这个旋转操作，就是qw'=q·qw·q^-1^. qw和qw'都是纯四元数，即实部为零，后三项对应的是xyz坐标。
* 好，以下进入possible_st_pointings_new函数。

  * mid的叉乘乘出来是个什么啊？*疑问保留*。答：似乎就是那个叉乘本身的意思，只不过后来用它来对应探测器的指向了。
  * map() 会根据提供的函数对指定序列做映射。`map(function, iterable, ...)`第一个参数 function 以参数序列中的每一个元素调用 function 函数，返回包含每次 function 函数返回值的新列表。返回值是map object类型。
  * Quaternion这个函数生成的旋转四元数就是上面的补充知识说的这一个。但是……为什么我试用下来它应该是以弧度制来接受'angle'的参数的？对没错就是这样，*这里有问题*。
  * 旋转操作.rotate不明。网上查不到文档和出处。内部查找结果，比较可信的是rotate(self, vector)方法。根据观察，它极大可能就是上面四元数知识里面的这种旋转。把这个输入向量按照四元数旋转操作旋转。输出结果为旋转后的向量。
  * 20201128以下。首先，四元数计算操作确认。Quaternion和rotate的用法就是上面写的那样。
  * mid_rot变量想要实现的应该是将mid向量绕目标所在的坐标（天球坐标）与原点所构成的旋转轴，旋转x角度。x从0到360，每10度算一次，一共36个。
  * np.linspace等差数列函数。相当于range(). 三个参数分别是start, end, length. 输出结果类型是np.ndarray.
  * 注意，文件里面的ra-dec都是转换成了弧度的。np的相关计算基本都是基于弧度的，比如sin, cos.
  * quat0里面的是一些四元数，分别对应36个mid_rot向量作为旋转轴，旋转角为（大概）卫星坐标系和天球坐标系的夹角w依次加上一些角度（0到15度，共五个），总计长度为180。
  * `quat = Quaternion(axis=target_pos_xyz, angle=i)`这个地方的angle又用成角度了，*应该转换成弧度*。
  * quat_r，把旋转变换成了quat·quat0的四元数。嗯……不确定这个计算的意义。似乎正式四元数的知识有欠缺。*需要问一下*。答：两个四元数相乘还是一个操作，就是复合，先做一个旋转，再做另一个旋转的意思。几何原理不明中。
  * 最后的输出就是detector&solar panet指向的一个序列。
  * 20201129注：角度问题已经修改。
* 关于时间问题：北京时间、utc、unix的区分：utc( Universal Time Coordinated ), 协调世界时。一种统一计时法。据unix时间戳词条介绍，Unix时间戳（英文为Unix epoch, Unix time, POSIX time 或 Unix timestamp）是从1970年1月1日（UTC/GMT的午夜）开始所经过的秒数，不考虑闰秒。北京时间与utc应该是相差八个时区。
* 直接从轨道文件中读取的orb_time_bj的格式是2020-11-18T23:59:50.000这种类型。后面的orb_time操作将其减去8个小时，并且转换成unix秒数格式，成为utc的标准形式。
* 接昨天，计算出detector&solar panet指向后，func.calc_st_radec计算星敏的指向，有一个18度夹角，比较简单。
* calculate_sunearth_angle函数顾名思义，就是计算星敏和日、地角度的。因为之前的possible_ra/dec有个对应360度旋转的第二维度，所以也要依次遍历计算。
* try-except-else，异常处理语法。运行try后面的语句，如果异常运行except, 没有异常运行else.
* 20201129组会：
  * 满足条件的姿态、限制条件具体是什么？这也是我没有看很懂的部分。对地心三轴稳定是什么意思？星敏什么时候有效？在这种状态下（对地心三轴稳定）轨道就可以确定姿态。
  * pobc、数据传输是个什么原理？
  * 目前收到的卫星姿态数据中四元数存在不连续变化情况，正在处理该问题。可能的原因是该时间段星敏没有工作，姿态是通过其他方式确定的。没有星敏数据的时间段应该如何准确得到卫星的状态？
  * 需要从遥测数据中获取星敏的有效数据。并且星敏可能存在“假有效”现象。这都是需要检验的部分。
  * 目前在**尽可能追求更长的开机时间，积累更多数据**，并且利用SAA（辐射异常区）的时间进行数据传输。天格可以随时开关机，没有加高压的准备时间，可以增大开机时间。极区也可以利用。
  * 天格并不是一个圆轨道，因此SAA区的数据可能是要根据轨道和太阳活动调整的。
  * 提出了展示卫星的实时轨道的想法。直接预测计算将来的轨道，然后实时“虚拟”展示。按：展示没必要所有东西都装在一个屏幕上，如果要画曲线可以画在另一个页面上。
* 昨天组会上提出的增加开机，利用极地等问题。MIN_HV_ON_TIME是否需要修改。按：已纳入考量。
* select_st_radec_new的选择条件似乎就是星敏和地球、太阳的夹角大于约定值。太阳能板与太阳的夹角小于约定值。原因：被遮挡的时候星敏不工作。所以无法控制指向。
* 想要了解的问题：

  * 关于现在时间段筛选的逻辑。应该是加入了人为调整。答：人为输入的是可以开机的时间段。目前是01:00-20:30。first是判断是否是第一轨，第一轨有些特殊。
  * 关于姿态选择的限制条件。见上面，就是这个。
  * 关于观测计划生成流程。几何以外的有哪些操作。答：如何使用服务器，需要学习linux。检查指令：原理上可以根据轨道、指令txt得到观测计划里绘制的两张图，用来检验计划是否正确。可能会有一些其他问题，具体情况具体分析。
  * 姿态控制时间之外的卫星应该设置成什么状态。答：磁控对日。可以在SAA之外开机。
  * 群里讨论的其他还有哪些需要注意的问题。
* 问题：关于没有解的情况。答：一般不会，可能有bug，目前设置成grid观测，指向虚拟源（正，背对地球）。