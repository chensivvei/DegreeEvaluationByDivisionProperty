from gurobipy import *
from MAXTERMS import *
import datetime
class Kreyvium(object):
	"""docstring for Kreyvium"""
	def __init__(self, obj_round, cand_deg, max_term, f, file_name):
		super(Kreyvium, self).__init__()
		self.round = obj_round
		self.cand_deg = cand_deg
		self.term = max_term
		self.f = f
		self.file_name = file_name
		self.variables = []

	def flag_xor(self, flag1, flag2):
		if flag1 == 0:
			res = flag2
		elif flag1 == 1:
			if flag2 == 1:
				res = 0
			elif flag2 == 0:
				res = 1
			else:
				res = 2
		else:
			res = 2
		return res

	def flag_and(self, flag1, flag2):
		if flag1 == 0:
			res = 0
		elif flag1 == 1:
			res = flag2
		else:
			if flag2 == 0:
				res = 0
			else:
				res = 2
		return res

	def division_copy(self, div_src, div_dst1, div_dst2):
		self.f.write(div_src+" - "+div_dst1+" - "+div_dst2+" = 0\n")

	def division_xor(self, div_src1, div_src2, div_src3, div_src4, div_dst):
		src = [div_src1, div_src2, div_src3, div_src4]
		self.f.write(" + ".join(src)+" - "+div_dst+" = 0\n")

	def division_and(self, div_src1, div_src2, div_dst, flag_dst):
		if flag_dst == 0:
			self.f.write(div_dst+" = 0\n")
		self.f.write(div_dst+" - "+div_src1+" >= 0\n")
		self.f.write(div_dst+" - "+div_src2+" >= 0\n")
		self.f.write(div_dst+" - "+div_src1+" - "+div_src2+" <= 0\n")

	def initial_state(self):
		v = ["v"+str(i) for i in range(128)]
		k = ["k"+str(i) for i in range(128)]
		sd = ["s"+str(i) for i in range(288)]
		sf = [2]*256+[1]*31+[0]
		Kd = ["K"+str(i) for i in range(128)]
		Kf = [2]*128
		IVd = ["IV"+str(i) for i in range(128)]
		IVf = [2]*128
		
		for i in range(128):
			self.f.write(sd[i+93]+" + "+IVd[127-i]+" - "+v[i]+" = 0\n")
			self.f.write(k[i]+" = 0\n")
			self.f.write(Kd[i]+" = 0\n")

		for i in range(93):
			self.f.write(sd[i]+" = 0\n")

		self.f.write(" + ".join(v)+" >= "+str(self.cand_deg+1)+"\n")
		self.variables = v + k + sd + Kd + IVd
		return (sd, sf, Kd, Kf, IVd, IVf)

	def state_update(self, sd, sf, Kd, Kf, IVd, IVf, t):
		copy_d = [["c"+str(t)+"_"+str(j)+"_"+str(i) for i in range(2)] for j in range(14)]
		and_d = ["a"+str(t)+"_"+str(i) for i in range(3)]
		xor_d = ["x"+str(t)+"_"+str(i) for i in range(3)]
		t_d = ["t"+str(t)+"_"+str(i) for i in range(2)]

		self.variables += and_d+xor_d+t_d

		copy_f = [[0 for i in range(2)] for j in range(14)]
		and_f = [0 for i in range(3)]
		xor_f = [0 for i in range(3)]
		t_f = [0]*2

		# x = s[242]+s[287]+s[285]*s[286]+s[68] #
		# y = s[65]+s[92]+s[90]*s[91]+s[170]
		# z = s[161]+s[176]+s[174]*s[175]+s[263] #
		index = [242, 285, 286, 68, 65, 90, 91, 170, 161, 174, 175, 263]
		last = [287, 92, 176]
		for rgst in range(3):
			s = 4*rgst
			e = s+4
			for i in range(s,e):
				self.variables += copy_d[i]
				self.division_copy(sd[index[i]], copy_d[i][0], copy_d[i][1])
				sd[index[i]] = copy_d[i][1]
				copy_f[i][0] = sf[index[i]]
				copy_f[i][1] = sf[index[i]]
			and_f[rgst] = self.flag_and(copy_f[s+1][0],copy_f[s+2][0])
			self.division_and(copy_d[s+1][0],copy_d[s+2][0],and_d[rgst],and_f[rgst])
			self.division_xor(copy_d[s][0],sd[last[rgst]],copy_d[s+3][0],and_d[rgst],xor_d[rgst])
			xor_f[rgst] = self.flag_xor(copy_f[s][0],sf[last[rgst]])
			xor_f[rgst] = self.flag_xor(xor_f[rgst], copy_f[s+3][0])
			xor_f[rgst] = self.flag_xor(xor_f[rgst], and_f[rgst])

		self.variables += copy_d[12] + copy_d[13]
		self.division_copy(Kd[0], copy_d[12][0], copy_d[12][1])
		self.division_copy(IVd[0], copy_d[13][0], copy_d[13][1])
		copy_f[12][0] = Kf[0]
		copy_f[12][1] = Kf[0]
		copy_f[13][0] = IVf[0]
		copy_f[13][1] = IVf[0]
		self.f.write(xor_d[0]+" + "+copy_d[12][0]+" - "+t_d[0]+" = 0\n")
		t_f[0] = self.flag_xor(xor_f[0], copy_f[12][0])
		self.f.write(xor_d[1]+" + "+copy_d[13][0]+" - "+t_d[1]+" = 0\n")
		t_f[1] = self.flag_xor(xor_f[1], copy_f[13][0])

		## update internal state ##
		for i in range(287):
			sd[287 - i] = sd[286 - i]
			sf[287 - i] = sf[286 - i]
		sd[0] = t_d[0]
		sf[0] = t_f[0]
		sd[93] = t_d[1]
		sf[93] = t_f[1]
		sd[177] = xor_d[2]
		sf[177] = xor_f[2]
		## update K', IV' ##
		for i in range(127):
			Kd[i] = Kd[i + 1]
			Kf[i] = Kf[i + 1]
			IVd[i] = IVd[i + 1]
			IVf[i] = IVf[i + 1]
		Kd[127] = copy_d[12][1]
		Kf[127] = copy_f[12][1]
		IVd[127] = copy_d[13][1]
		IVf[127] = copy_f[13][1]


	def output_bit(self):
		(sd, sf, Kd, Kf, IVd, IVf) = self.initial_state()
		for t in range(self.round):
			self.state_update(sd,sf,Kd,Kf,IVd,IVf,t)
		for i in range(128):
			if 543-i in self.term:
				self.f.write(IVd[i]+" <= 1\n")
			else:
				self.f.write(IVd[i]+" = 0\n")
			self.f.write(Kd[i]+" = 0\n")
		for i in range(288):
			if i in self.term:
				self.f.write(sd[i]+" <= 1\n")
			else:
				self.f.write(sd[i]+" = 0\n")


	def obj_function(self):
		self.f.write("Maximize\n")
		v = ["v"+str(i) for i in range(128)]
		self.f.write(" + ".join(v)+"\n")

	def constraints(self):
		self.f.write("Subject To\n")
		self.output_bit()

	def var_type(self):
		self.f.write("Binary\n")
		self.f.write("\n".join(self.variables)+"\nEnd\n")

	def creat_model(self):
		self.obj_function()
		self.constraints()
		self.var_type()

	def solve_model(self):
		model = read(self.file_name)
		#model.Params.Threads = 30
		#model.Params.OutputFlag = 0
		model.optimize()
		if model.Status == 2:
			obj_var = model.getObjective()
			obj_value = obj_var.getValue()
			return int(obj_value)
		else:
			return 0
			
def main():
	file_name = "Kreyvium.lp"
	t2 = 225
	for r in range(t2+1, 1153):
		degree = 0
		t1 = r - t2
		start = datetime.datetime.now()
		for term in max_terms:
			print("========================================= "+str(max_terms.index(term)+1)+" ====================================\n")
			f = open(file_name,"w")
			kreyvium = Kreyvium(t1, degree, term, f, file_name)
			kreyvium.creat_model()
			f.close()
			obj_value = kreyvium.solve_model()
			if degree < obj_value:
				degree = obj_value
		end = datetime.datetime.now()
		fp = open("result.txt","a")
		fp.write("round = "+str(r)+", degree = "+str(degree)+", time = "+str(end-start)+" s\n")
		fp.close()

if __name__ == '__main__':
	main()











